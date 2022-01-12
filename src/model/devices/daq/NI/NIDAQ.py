"""
NI DAQ Class
Model class for controlling National Instruments DAQ devices.
Adopted and modified from mesoSPIM.
"""
# Standard Imports
import os
import numpy as np
import csv
import time

# Third Party Imports
import nidaqmx
from nidaqmx.constants import AcquisitionType, TaskMode
from nidaqmx.constants import LineGrouping, DigitalWidthUnits
from nidaqmx.types import CtrTime

# Local Imports
from model.devices.daq.waveforms import *
from model.devices.daq.DAQBase import DAQBase as DAQBase

class DAQ(DAQBase):
    def __init__(self, model, etl_constants_path, verbose):
        self.verbose = verbose
        self.etl_constants = session(etl_constants_path, self.verbose)

    def calculate_samples(self, model):
        '''
        # Calculate the number of samples for the waveforms.
        # Simply the sampling frequency times the duration of the waveform.
        '''
        samplerate = model.StartupParameters.samplerate
        sweeptime = model.StartupParameters.sweeptime
        self.samples = int(samplerate*sweeptime)
        if self.verbose:
            print('Number of samples: ' + str(self.samples))

    def create_waveforms(self):
        '''
        # Create the waveforms for the ETL, Galvos, and Lasers.
        '''

        self.calculate_samples()
        self.create_etl_waveforms()
        self.create_galvo_waveforms()
        self.create_laser_waveforms()

        # Bundle the waveforms into a single waveform.
        self.bundle_galvo_and_etl_waveforms()

    def create_etl_waveforms(self):
        '''
        # Create the waveforms for the Electrotunable Lens
        '''
        # Get the parameters for the ETL waveforms.
        samplerate = model.StartupParameters.samplerate
        sweeptime = model.StartupParameters.sweeptime
        etl_l_delay = model.ETLParameters.etl_l_delay_percent
        etl_l_ramp_rising = model.ETLParameters.etl_l_ramp_rising_percent
        etl_l_ramp_falling = model.ETLParameters.etl_l_ramp_falling_percent
        etl_l_amplitude = model.ETLParameters.etl_l_amplitude
        etl_l_offset = model.ETLParameters.etl_l_offset

        # Calculate the ETL waveforms.
        self.etl_l_waveform = tunable_lens_ramp(samplerate=samplerate,
                                                sweeptime=sweeptime,
                                                delay=etl_l_delay,
                                                rise=etl_l_ramp_rising,
                                                fall=etl_l_ramp_falling,
                                                amplitude=etl_l_amplitude,
                                                offset=etl_l_offset)

    def create_low_res_galvo_waveforms(self):
        '''
        # Calculate the sawtooth waveforms for the low-resolution digitally scanned galvo.
        '''
        # Get the parameters for the galvo waveforms.
        samplerate = model.StartupParameters.samplerate
        sweeptime = model.StartupParameters.sweeptime
        galvo_l_frequency = model.GalvoParameters.galvo_l_frequency
        galvo_l_amplitude = model.GalvoParameters.galvo_l_amplitude
        galvo_l_offset = model.GalvoParameters.galvo_l_offset
        galvo_l_duty_cycle = model.GalvoParameters.galvo_l_duty_cycle
        galvo_l_phase = model.GalvoParameters.galvo_l_phase

        # Calculate the galvo waveforms.
        self.galvo_l_waveform = sawtooth(samplerate=samplerate,
                                         sweeptime=sweeptime,
                                         frequency=galvo_l_frequency,
                                         amplitude=galvo_l_amplitude,
                                         offset=galvo_l_offset,
                                         dutycycle=galvo_l_duty_cycle,
                                         phase=galvo_l_phase)

    def create_high_res_galvo_waveforms(self):
        '''
        # Calculate the DC waveform for the resonant galvanometer drive signal.
        '''
        # Get the parameters for the galvo waveforms.
        samplerate = model.StartupParameters.samplerate
        sweeptime = model.StartupParameters.sweeptime
        galvo_amplitude = model.GalvoParameters.galvo_r_amplitude

        # Calculate the galvo waveforms.
        self.galvo_r_waveform = dc_value(samplerate=samplerate,
                                         sweeptime=sweeptime,
                                         amplitude=galvo_r_amplitude,
                                         offset=0)

    def create_laser_waveforms(self):
        '''
        # Calculate the waveforms for the lasers.
        # Digital output for on/off.
        # Analog output for intensity control
        # Digital output for left or right fiber.
        '''
        samplerate = model.StartupParameters.samplerate
        sweeptime = model.StartupParameters.sweeptime

        # Get the laser parameters.
        laser_l_delay = model.StartupParameters.laser_l_delay
        laser_l_pulse = model.StartupParameters.laser_l_pulse
        max_laser_voltage = model.StartupParameters.laser_max_ao
        intensity = model.StartupParameters.intensity

        # Create a zero waveform
        self.zero_waveform = np.zeros((self.samples))

        # Update the laser intensity waveform
        # This could be improved: create a list with as many zero arrays as analog out lines for ETL and Lasers
        self.laser_waveform_list = [self.zero_waveform for i in self.cfg.laser_designation]

        # Convert from intensity to voltage
        laser_voltage = max_laser_voltage * intensity / 100

        self.laser_template_waveform = single_pulse(samplerate=samplerate,
                                                    sweeptime=sweeptime,
                                                    delay=laser_l_delay,
                                                    pulsewidth=laser_l_pulse,
                                                    amplitude=laser_voltage,
                                                    offset=0)

        #TODO: basically just sends out the signal to the one channel that matters.

        # # The key: replace the waveform in the waveform list with this new template
        # current_laser_index = self.cfg.laser_designation[self.state['laser']]
        # self.laser_waveform_list[current_laser_index] = self.laser_template_waveform
        # self.laser_waveforms = np.stack(self.laser_waveform_list)

    def bundle_galvo_and_etl_waveforms(self):
        '''
        # Stacks the Galvo and ETL waveforms into a numpy array adequate for
        # the NI cards. In here, the assignment of output channels of the Galvo / ETL card to the
        # corresponding output channel is hardcoded: This could be improved.
        '''
        self.galvo_and_etl_waveforms = np.stack((self.galvo_l_waveform,
                                                 self.galvo_r_waveform,
                                                 self.etl_l_waveform,
                                                 self.etl_r_waveform))

    def update_etl_parameters_from_zoom(self, zoom):
        '''
        # Little helper method: Because the multiscale core is not handling
        # the serial Zoom connection.
        '''
        laser = self.state['laser']
        etl_cfg_file = self.state['ETL_cfg_file']
        self.update_etl_parameters_from_csv(etl_cfg_file, laser, zoom)

    def update_etl_parameters_from_laser(self, laser):
        '''
        # Little helper method: Because laser changes need an ETL parameter update
        '''
        zoom = self.state['zoom']
        etl_cfg_file = self.state['ETL_cfg_file']
        self.update_etl_parameters_from_csv(etl_cfg_file, laser, zoom)

    def create_tasks(self):
        '''
        Creates a total of four tasks for the microscope:
        These are:
        - the master trigger task, a digital out task that only provides a trigger pulse for the others
        - the camera trigger task, a counter task that triggers the camera in lightsheet mode
        - the galvo task (analog out) that controls the left & right galvos for creation of
          the light-sheet and shadow avoidance
        - the ETL & Laser task (analog out) that controls all the laser intensities (Laser should only
          be on when the camera is acquiring) and the left/right ETL waveforms
        '''

        # TODO: Get the Acquisition Hardware from the Configuration File
        ah = self.cfg.acquisition_hardware

        self.calculate_samples()
        samplerate, sweeptime = self.state.get_parameter_list(['samplerate','sweeptime'])
        samples = self.samples
        camera_pulse_percent, camera_delay_percent = self.state.get_parameter_list(['camera_pulse_percent','camera_delay_percent'])

        # Create the master trigger, camera trigger, etl, and laser tasks
        self.master_trigger_task = nidaqmx.Task()
        self.camera_trigger_task = nidaqmx.Task()
        self.galvo_etl_task = nidaqmx.Task()
        self.laser_task = nidaqmx.Task()

        # Set up the DO master trigger task
        self.master_trigger_task.do_channels.add_do_chan(ah['master_trigger_out_line'],
                                                         line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)

        # Calculate camera high time and initial delay.
        # Disadvantage: high time and delay can only be set after a task has been created
        self.camera_high_time = camera_pulse_percent*0.01*sweeptime
        self.camera_delay = camera_delay_percent*0.01*sweeptime

        # Set up the camera trigger
        self.camera_trigger_task.co_channels.add_co_pulse_chan_time(ah['camera_trigger_out_line'],
                                                                    high_time=self.camera_high_time,
                                                                    initial_delay=self.camera_delay)

        # Configure camera to be triggered by the master trigger
        self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(ah['camera_trigger_source'])

        # Set up the Galvo and setting the trigger input
        self.galvo_etl_task.ao_channels.add_ao_voltage_chan(ah['galvo_etl_task_line'])
        self.galvo_etl_task.timing.cfg_samp_clk_timing(rate=samplerate,
                                                   sample_mode=AcquisitionType.FINITE,
                                                   samps_per_chan=samples)

        # Set up the ETL to be triggered by the master trigger
        self.galvo_etl_task.triggers.start_trigger.cfg_dig_edge_start_trig(ah['galvo_etl_task_trigger_source'])

        # Set up the ETL and lasers
        self.laser_task.ao_channels.add_ao_voltage_chan(ah['laser_task_line'])
        self.laser_task.timing.cfg_samp_clk_timing(rate=samplerate,
                                                    sample_mode=AcquisitionType.FINITE,
                                                    samps_per_chan=samples)

        # Configure ETL and Lasers to ber triggered by the master trigger
        self.laser_task.triggers.start_trigger.cfg_dig_edge_start_trig(ah['laser_task_trigger_source'])

    def write_waveforms_to_tasks(self):
        '''
        Write the waveforms to the slave tasks
        '''
        self.galvo_etl_task.write(self.galvo_and_etl_waveforms)
        self.laser_task.write(self.laser_waveforms)

    def start_tasks(self):
        '''
        Start the tasks for camera triggering and analog outputs
        If the tasks are configured to be triggered, they won't output any signals until run_tasks() is called.
        '''
        self.camera_trigger_task.start()
        self.galvo_etl_task.start()
        self.laser_task.start()

    def run_tasks(self):
        '''
        Run the tasks for triggering, analog and counter outputs.
        the master trigger initiates all other tasks via a shared trigger
        For this to work, all analog output and counter tasks have to be started so
        that they are waiting for the trigger signal.
        '''

        self.master_trigger_task.write([False, True, True, True, False], auto_start=True)
        # Wait until waveforms have been output
        self.galvo_etl_task.wait_until_done()
        self.laser_task.wait_until_done()
        self.camera_trigger_task.wait_until_done()

    def stop_tasks(self):
        # Stop the tasks for triggering, analog and counter outputs.
        self.galvo_etl_task.stop()
        self.laser_task.stop()
        self.camera_trigger_task.stop()
        self.master_trigger_task.stop()

    def close_tasks(self):
        # Close the tasks for triggering, analog, and counter outputs.
        self.galvo_etl_task.close()
        self.laser_task.close()
        self.camera_trigger_task.close()
        self.master_trigger_task.close()

if (__name__ == "__main__"):
    print("Testing Mode - WaveFormGenerator Class")
    print(constants.AcquisitionHardware.hardware_type)