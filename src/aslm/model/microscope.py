# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import logging
from multiprocessing.managers import ListProxy

from aslm.model.device_startup_functions import start_camera, start_filter_wheel, start_zoom, start_shutter, start_remote_focus_device, start_galvo, start_lasers, start_stage
from aslm.tools.common_functions import build_ref_name

p = __name__.split(".")[1]
logger = logging.getLogger(p)

class Microscope:
    def __init__(self, name, configuration, devices_dict, is_synthetic=False):
        self.microscope_name = name
        self.configuration = configuration
        self.data_buffer = None
        self.stages = {}
        self.lasers = {}
        self.galvo = {}
        self.daq = devices_dict.get('daq', None)

        device_ref_dict = {
            'camera': ['type', 'serial_number'],
            'filter_wheel': ['type'],
            'zoom': ['type', 'servo_id'],
            'shutter': ['type', 'channel'],
            'remote_focus_device': ['type', 'channel'],
            'galvo': ['type', 'channel'],
            'lasers': ['wavelength']
        }

        device_name_dict = {
            'lasers': 'wavelength'
        }

        laser_list = self.configuration['configuration']['microscopes'][self.microscope_name]['lasers']
        self.laser_wavelength = [laser['wavelength'] for laser in laser_list]

        # load/start all the devices listed in device_ref_dict
        for device_name in device_ref_dict.keys():
            device_connection = None
            device_config_list = []
            device_name_list = []

            if type(configuration['configuration']['microscopes'][name][device_name]) == ListProxy:
                i = 0
                for d in configuration['configuration']['microscopes'][name][device_name]:
                    device_config_list.append(d)
                    if device_name in device_name_dict:
                        device_name_list.append(build_ref_name('_', d[device_name_dict[device_name]]))
                    else:
                        device_name_list.append(build_ref_name('_', device_name, i))
                    i += 1
                
                is_list = True
            else:
                device_config_list.append(configuration['configuration']['microscopes'][name][device_name])
                is_list = False
            
            for i, device in enumerate(device_config_list):
                device_ref_name = None
                if 'hardware' in device.keys():
                    ref_list = [device['hardware'][k] for k in device_ref_dict[device_name]]
                else:
                    try:
                        ref_list = [device[k] for k in device_ref_dict[device_name]]
                    except:
                        ref_list = []
                
                device_ref_name = build_ref_name('_', *ref_list)

                if device_name in devices_dict and device_ref_name in devices_dict[device_name]:
                    device_connection = devices_dict[device_name][device_ref_name]
                elif (device_ref_name.startswith('NI') and (device_name == 'galvo' or device_name == 'remote_focus_device')):
                    # TODO: Remove this. We should not have this hardcoded.
                    device_connection = self.daq

                if is_list:
                    exec(f"self.{device_name}['{device_name_list[i]}'] = start_{device_name}(name, device_connection, configuration, i, is_synthetic)")
                else:
                    exec(f'self.{device_name} = start_{device_name}(name, device_connection, configuration, is_synthetic)')
                
                if device_connection is None and device_ref_name != None:
                    if device_name not in devices_dict:
                        devices_dict[device_name] = {}
                    devices_dict[device_name][device_ref_name] = getattr(self, device_name)[device_name_list[i]] if is_list else getattr(self, device_name)

        # stages
        stage_devices = self.configuration['configuration']['microscopes'][self.microscope_name]['stage']['hardware']
        if type(stage_devices) != ListProxy:
            stage_devices = [stage_devices]
        for i, device_config in enumerate(stage_devices):
            device_ref_name = build_ref_name('_', device_config['type'], device_config['serial_number'])
            if device_ref_name not in devices_dict['stages']:
                logger.debug('stage has not been loaded!')
                raise Exception('no stage device!')
            if device_ref_name.startswith('GalvoNIStage'):
                # TODO: Remove this. We should not have this hardcoded.
                devices_dict['stages'][device_ref_name] = self.daq
            stage = start_stage(self.microscope_name, devices_dict['stages'][device_ref_name], self.configuration, i, is_synthetic)
            for axes in device_config['axes']:
                self.stages[axes] = stage

        # connect daq and camera in synthetic mode
        if is_synthetic:
            self.daq.add_camera(self.microscope_name, self.camera)

    def update_data_buffer(self, img_width, img_height, data_buffer, number_of_frames):
        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.camera.set_ROI(img_width, img_height)
        self.data_buffer = data_buffer
        self.number_of_frames = number_of_frames

    def move_stage_offset(self, former_microscope=None):
        if former_microscope:
            former_offset_dict = self.configuration['configuration']['microscopes'][former_microscope]['stage']
        else:
            former_offset_dict = dict((f'{a}_offset', 0) for a in self.stages)
        self_offset_dict = self.configuration['configuration']['microscopes'][self.microscope_name]['stage']
        pos_dict = self.get_stage_position()
        for axes in self.stages:
            pos = pos_dict[axes+'_pos'] + self_offset_dict[axes+'_offset'] - former_offset_dict[axes+'_offset']
            self.stages[axes].move_absolute({axes+'_pos': pos}, wait_until_done=True)

    def prepare_acquisition(self):
        if self.camera.camera_controller.is_acquiring:
            self.camera.close_image_series()
        # Set Camera Sensor Mode - Must be done before camera is initialized.
        sensor_mode = self.configuration['experiment']['CameraParameters']['sensor_mode']
        self.camera.set_sensor_mode(sensor_mode)
        if sensor_mode == 'Light-Sheet':
            self.camera.set_readout_direction(self.configuration['experiment']['CameraParameters']['readout_direction'])
        # Initialize Image Series - Attaches camera buffer and start imaging
        self.camera.initialize_image_series(self.data_buffer,
                                            self.number_of_frames)
        # calculate all the waveform
        self.shutter.open_shutter()
        return self.calculate_all_waveform()

    def end_acquisition(self):
        if self.camera.is_acquiring:
            self.camera.close_image_series()
        self.shutter.close_shutter()
        for k in self.lasers:
            self.lasers[k].turn_off()

    def calculate_all_waveform(self):
        readout_time = self.get_readout_time()
        camera_waveform = self.daq.calculate_all_waveforms(self.microscope_name, readout_time)
        etl_waveform = self.remote_focus_device.adjust(readout_time)
        galvo_waveform = [self.galvo[k].adjust(readout_time) for k in self.galvo]
        waveform_dict = {
            'camera_waveform': camera_waveform,
            'etl_waveform': etl_waveform,
            'galvo_waveform': galvo_waveform
        }
        return waveform_dict

    def prepare_channel(self, channel_key):
        channel = self.configuration['experiment']['MicroscopeState']['channels'][channel_key]
        # Filter Wheel Settings.
        self.filter_wheel.set_filter(channel['filter'])

        # Camera Settings
        self.current_exposure_time = channel['camera_exposure_time']
        if self.configuration['experiment']['CameraParameters']['sensor_mode'] == 'Light-Sheet':
            self.current_exposure_time, self.camera_line_interval = self.camera.calculate_light_sheet_exposure_time(
                self.current_exposure_time,
                int(self.configuration['experiment']['CameraParameters']['number_of_pixels']))
            self.camera.set_exposure_time(self.current_exposure_time)
            self.camera.camera_controller.set_property_value("internal_line_interval", self.camera_line_interval)

        # Laser Settings
        current_laser_index = channel['laser_index']
        self.lasers[str(self.laser_wavelength[current_laser_index])].set_power(channel['laser_power'])
        for k in self.lasers:
            self.lasers[k].turn_off()
        self.lasers[str(self.laser_wavelength[current_laser_index])].turn_on()

    def get_readout_time(self):
        r"""Get readout time from camera.

        Get the camera readout time if we are in normal mode.
        Return a -1 to indicate when we are not in normal mode.
        This is needed in daq.calculate_all_waveforms()

        Returns
        -------
        readout_time : float
            Camera readout time in seconds or -1 if not in Normal mode.
        """
        readout_time = 0
        if self.configuration['experiment']['CameraParameters']['sensor_mode'] == 'Normal':
            readout_time = self.camera.camera_controller.get_property_value("readout_time")
        return readout_time

    def move_stage(self, pos_dict, wait_until_done=False):
        success = True
        for pos_axis in pos_dict:
            axis = pos_axis[:pos_axis.index('_')]
            success = success and self.stages[axis].move_absolute({pos_axis: pos_dict[pos_axis]}, wait_until_done)
        return success

    def stop_stage(self):
        for axis in self.stages:
            self.stages[axis].stop()

    def get_stage_position(self):
        ret_pos_dict = {}
        for axis in self.stages:
            pos_axis = axis + '_pos'
            temp_pos = self.stages[axis].report_position()
            ret_pos_dict[pos_axis] = temp_pos[pos_axis]
        return ret_pos_dict
