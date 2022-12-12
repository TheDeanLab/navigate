import logging
import time
from multiprocessing.managers import ListProxy

from aslm.model.devices.stages.stage_base import StageBase

from aslm.model.waveforms import dc_value, tunable_lens_ramp

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class GalvoNIStage(StageBase):
    def __init__(self, microscope_name, device_connection, configuration, device_id=0):
        super().__init__(microscope_name, device_connection, configuration, device_id)

        # 1 V/ 100 um
        device_config = configuration['configuration']['microscopes'][microscope_name]['stage']['hardware']

        # eval(self.volts_per_micron, {"x": 100})
        if type(device_config) == ListProxy:
            self.volts_per_micron = device_config[device_id]['volts_per_micron']
            self.axes_channels = device_config[device_id]['axes_channels']
            self.galvo_max_voltage = device_config[device_id]['max']
            self.galvo_min_voltage = device_config[device_id]['min']
        else:
            self.volts_per_micron = device_config['volts_per_micron']
            self.axes_channels = device_config['axes_channels']
            self.galvo_max_voltage = device_config['max']
            self.galvo_min_voltage = device_config['min']

        self.daq = device_connection

        self.microscope_name = microscope_name
        self.configuration = configuration

        self.trigger_source = configuration['configuration']['microscopes'][microscope_name]['daq']['trigger_source']
        self.camera_delay_percent = configuration['configuration']['microscopes'][microscope_name]['camera']['delay_percent']
        self.etl_ramp_falling = configuration['configuration']['microscopes'][microscope_name]['remote_focus_device']['ramp_falling_percent']

        self.waveform_dict = {}
        for k in configuration['configuration']['gui']['channels'].keys():
            self.waveform_dict[k] = None

    # for stacking, we could have 2 axis here or not, y is for tiling, not necessary
    def report_position(self):
        self.update_position_dictionaries()

        return self.position_dict

    def move_axis_absolute(self, axis, axis_num, move_dictionary):
        """
        Implement movement logic along a single axis.

        Example calls:

        Parameters
        ----------
        axis : str
            An axis prefix in move_dictionary. For example, axis='x' corresponds to 'x_abs', 'x_min', etc.
        axis_num : int
            The corresponding number of this axis on a PI stage.
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', 'x_min', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.

        Returns
        -------
        bool
            Was the move successful?
        """
        self.waveform_dict = dict.fromkeys(self.waveform_dict, None)
        axis_abs = self.get_abs_position(axis, move_dictionary)
        if axis_abs == -1e50:
            return False

        volts = eval(self.volts_per_micron, {"x": axis_abs})

        microscope_state = self.configuration['experiment']['MicroscopeState']
        self.sample_rate = self.configuration['configuration']['microscopes'][self.microscope_name]['daq']['sample_rate']

        for channel_key in microscope_state['channels'].keys():
            # channel includes 'is_selected', 'laser', 'filter', 'camera_exposure'...
            channel = microscope_state['channels'][channel_key]

            # Only proceed if it is enabled in the GUI
            if channel['is_selected'] is True:

                # Get the Waveform Parameters - Assumes ETL Delay < Camera Delay.  Should Assert.
                exposure_time = channel['camera_exposure_time'] / 1000
                self.sweep_time = exposure_time + exposure_time * ((self.camera_delay_percent + self.etl_ramp_falling) / 100)
                readout_time = 0  # TODO: find a way to pass this to the stages
                if readout_time > 0:
                    # This addresses the dovetail nature of the camera readout in normal mode. The camera reads middle
                    # out, and the delay in start of the last lines compared to the first lines causes the exposure
                    # to be net longer than exposure_time. This helps the galvo keep sweeping for the full camera
                    # exposure time.
                    self.sweep_time += readout_time
                self.samples = int(self.sample_rate * self.sweep_time)

                # Calculate the Waveforms
                if self.configuration['experiment']['MicroscopeState']['image_mode'] == 'projection':
                    z_start = self.configuration['experiment']['MicroscopeState']['abs_z_start']
                    z_end = self.configuration['experiment']['MicroscopeState']['abs_z_end']
                    amp = eval(self.volts_per_micron, {"x": 0.5*(z_end-z_start)})
                    off = eval(self.volts_per_micron, {"x": 0.5*(z_end+z_start)})
                    self.waveform_dict[channel_key] = tunable_lens_ramp(sample_rate=self.sample_rate,
                                                                        exposure_time=exposure_time,
                                                                        sweep_time=self.sweep_time,
                                                                        etl_delay=7.5,
                                                                        camera_delay=self.camera_delay_percent,
                                                                        fall=self.etl_ramp_falling,
                                                                        amplitude=amp,
                                                                        offset=off)                                                    
                elif self.configuration['experiment']['MicroscopeState']['image_mode'] == 'confocal-projection':
                    z_range = self.configuration['experiment']['MicroscopeState']['scanrange']
                    z_offset_start = self.configuration['experiment']['MicroscopeState']['offset_start']
                    z_offset_end = self.configuration['experiment']['MicroscopeState']['offset_end']
                    z_planes = self.configuration['experiment']['MicroscopeState']['n_plane']
                    if z_planes == 1:
                        amp = eval(self.volts_per_micron, {"x": 0.5*(z_range)})
                        off = eval(self.volts_per_micron, {"x": 0.5*(z_offset_start)})
                    else:
                        amp = eval(self.volts_per_micron, {"x": 0.5*(z_range)})
                        off = eval(self.volts_per_micron, {"x": 0.5*(z_offset_end)})
                    self.waveform_dict[channel_key] = tunable_lens_ramp(sample_rate=self.sample_rate,
                                                                        exposure_time=exposure_time,
                                                                        sweep_time=self.sweep_time,
                                                                        etl_delay=7.5,
                                                                        camera_delay=self.camera_delay_percent,
                                                                        fall=self.etl_ramp_falling,
                                                                        amplitude=amp,
                                                                        offset=off)
                else:
                    self.waveform_dict[channel_key] = dc_value(sample_rate=self.sample_rate,
                                                            sweep_time=self.sweep_time,
                                                            amplitude=volts)
                self.waveform_dict[channel_key][self.waveform_dict[channel_key] > self.galvo_max_voltage] = self.galvo_max_voltage
                self.waveform_dict[channel_key][self.waveform_dict[channel_key] < self.galvo_min_voltage] = self.galvo_min_voltage

        self.daq.analog_outputs[self.axes_channels[axis_num]] = {'sample_rate': self.sample_rate,
                                                                 'samples': self.samples,
                                                                 'trigger_source': self.trigger_source,
                                                                 'waveform': self.waveform_dict}
        return True

    def move_absolute(self, move_dictionary, wait_until_done=False):
        """

        Parameters
        ----------
        move_dictionary : dict
            A dictionary of values required for movement. Includes 'x_abs', etc. for one or more axes.
            Expects values in micrometers, except for theta, which is in degrees.
        wait_until_done : bool
            Block until stage has moved to its new spot.

        Returns
        -------
        success : bool
            Was the move successful?
        """

        for i, ax in enumerate(self.axes):
            success = self.move_axis_absolute(ax, i, move_dictionary)
            if success and wait_until_done is True:
                stage_pos, n_tries, i = -1e50, 10, 0
                target_pos = move_dictionary[f"{ax}_abs"] - getattr(self, f"int_{ax}_pos_offset",
                                                                    0)  # TODO: should we default to 0?
                while (abs(stage_pos - target_pos) < 0.01) and (i < n_tries):
                    #replace: stage_pos = self.mcl_controller.MCL_SingleReadN(ax, self.handle)
                    #todo: include a call to the NI board to set a voltage
                    i += 1
                    time.sleep(0.01)
                if abs(stage_pos - target_pos) > 0.01:
                    success = False

        return success
    
