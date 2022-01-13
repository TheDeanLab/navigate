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
    def __init__(self, model, etl_constants_path, verbose=False):
        self.verbose = verbose
        self.etl_constants = session(etl_constants_path, self.verbose)
        self.model = model

    def calculate_samples(self):
        '''
        # Calculate the number of samples for the waveforms.
        # Simply the sampling frequency times the duration of the waveform.
        '''
        self.samplerate = self.model.configuration.StartupParameters.samplerate
        self.sweeptime = self.model.configuration.StartupParameters.sweeptime
        self.samples = int(self.samplerate * self.sweeptime)
        if self.verbose:
            print('Number of samples: ' + str(self.samples))

    def identify_laser_idx(self):
        '''
        # This is probably a terrible way to do it. Basically hard-coded.
        '''
        # 488 index = 0. 562 index = 1. 642 index = 2.
        current_laser = self.model.experiment.current_laser
        if current_laser == '488nm':
            self.laser_idx = 0
        elif current_laser == '562nm':
            self.laser_idx = 1
        elif current_laser == '642nm':
            self.laser_idx = 2
        else:
            print("Laser Index Not Found")

    def create_waveforms(self):
        '''
        # Create the waveforms for the ETL, Galvos, and Lasers.
        '''
        self.calculate_samples()

        # ETL
        self.create_etl_waveform()

        # Galvos
        self.create_high_res_galvo_waveform()
        self.create_low_res_galvo_waveform()

        # Lasers
        self.create_analog_laser_waveforms()
        self.create_digital_laser_waveforms()
        self.create_laser_switching_waveform()

        # Bundle the waveforms into a single waveform.
        self.bundle_galvo_and_etl_waveforms()

    def create_etl_waveform(self):
        '''
        # Create the waveforms for the Electrotunable Lens
        '''
        # Get the parameters for the ETL waveforms.
        samplerate = self.model.configuration.StartupParameters.samplerate
        sweeptime = self.model.configuration.StartupParameters.sweeptime
        etl_l_delay = self.model.ETLParameters.etl_l_delay_percent
        etl_l_ramp_rising = self.model.ETLParameters.etl_l_ramp_rising_percent
        etl_l_ramp_falling = self.model.ETLParameters.etl_l_ramp_falling_percent
        etl_l_amplitude = self.model.ETLParameters.etl_l_amplitude
        etl_l_offset = self.model.ETLParameters.etl_l_offset

        # Calculate the ETL waveforms.
        self.etl_l_waveform = tunable_lens_ramp(samplerate=samplerate,
                                                sweeptime=sweeptime,
                                                delay=etl_l_delay,
                                                rise=etl_l_ramp_rising,
                                                fall=etl_l_ramp_falling,
                                                amplitude=etl_l_amplitude,
                                                offset=etl_l_offset)

    def create_low_res_galvo_waveform(self):
        '''
        # Calculate the sawtooth waveforms for the low-resolution digitally scanned galvo.
        '''
        # Get the parameters for the galvo waveforms.
        samplerate = self.model.configuration.StartupParameters.samplerate
        sweeptime = self.model.configuration.StartupParameters.sweeptime
        galvo_l_frequency = self.model.GalvoParameters.galvo_l_frequency
        galvo_l_amplitude = self.model.GalvoParameters.galvo_l_amplitude
        galvo_l_offset = self.model.GalvoParameters.galvo_l_offset
        galvo_l_duty_cycle = self.model.GalvoParameters.galvo_l_duty_cycle
        galvo_l_phase = self.model.GalvoParameters.galvo_l_phase

        # Calculate the galvo waveforms.
        self.galvo_l_waveform = sawtooth(samplerate=samplerate,
                                         sweeptime=sweeptime,
                                         frequency=galvo_l_frequency,
                                         amplitude=galvo_l_amplitude,
                                         offset=galvo_l_offset,
                                         dutycycle=galvo_l_duty_cycle,
                                         phase=galvo_l_phase)

    def create_high_res_galvo_waveform(self):
        '''
        # Calculate the DC waveform for the resonant galvanometer drive signal.
        '''
        # Get the parameters for the galvo waveforms.
        samplerate = self.model.configuration.StartupParameters.samplerate
        sweeptime = self.model.configuration.StartupParameters.sweeptime
        galvo_amplitude = self.model.GalvoParameters.galvo_r_amplitude

        # Calculate the galvo waveforms.
        self.galvo_r_waveform = dc_value(samplerate=samplerate,
                                         sweeptime=sweeptime,
                                         amplitude=galvo_r_amplitude,
                                         offset=0)

    def create_laser_switching_waveform(self):
        '''
        # TTL for switching between laser fibers.
        # 0V is the left fiber, 5V is the right.
        '''
        samplerate = self.model.configuration.StartupParameters.samplerate
        sweeptime = self.model.configuration.StartupParameters.sweeptime

        fiber_idx = self.model.experiment.fiber
        if fiber_idx == 0:
            amplitude = self.model.configuration.laser_min_do
        else:
            amplitude = self.model.configuration.laser_max_do

        self.laser_switching_waveform = dc_value(samplerate=samplerate,
                                                 sweeptime=sweeptime,
                                                 amplitude=amplitude,
                                                 offset=0)

    def create_analog_laser_waveforms(self):
        '''
        # Calculate the waveforms for the lasers.
        # Analog output for intensity control
        # Digital output for left or right fiber.
        '''
        samplerate = self.model.configuration.StartupParameters.samplerate
        sweeptime = self.model.configuration.StartupParameters.sweeptime

        # Get the laser parameters.
        laser_l_delay = self.model.configuration.StartupParameters.laser_l_delay
        laser_l_pulse = self.model.configuration.StartupParameters.laser_l_pulse

        # Convert from intensity to voltage
        max_laser_voltage = self.model.DAQParameters.laser_max_ao
        intensity = self.model.configuration.StartupParameters.intensity
        laser_voltage = max_laser_voltage * intensity / 100

        self.laser_template_waveform = single_pulse(samplerate=samplerate,
                                                    sweeptime=sweeptime,
                                                    delay=laser_l_delay,
                                                    pulsewidth=laser_l_pulse,
                                                    amplitude=laser_voltage,
                                                    offset=0)
        # Pre-allocate the waveforms.
        # This could be improved: create a list with as many zero arrays as analog out lines for ETL and Lasers
        self.identify_laser_idx()
        self.laser_waveform_list = [np.zeros((self.samples)) for i in self.model.DAQParameters.number_of_lasers]
        self.laser_waveform_list[self.laser_idx] = self.laser_template_waveform
        self.laser_ao_waveforms = np.stack(self.laser_waveform_list)

    def create_digital_laser_waveforms(self):
        '''
        # Calculate the waveforms for the lasers.
        # Digital output for on/off.
        # Digital output for left or right fiber.
        '''
        samplerate = self.model.configuration.StartupParameters.samplerate
        sweeptime = self.model.configuration.StartupParameters.sweeptime

        # Get the laser parameters.
        laser_l_delay = self.model.configuration.StartupParameters.laser_l_delay
        laser_l_pulse = self.model.configuration.StartupParameters.laser_l_pulse

        max_laser_voltage = self.model.DAQParameters.laser_max_do

        self.laser_template_waveform = single_pulse(samplerate=samplerate,
                                                    sweeptime=sweeptime,
                                                    delay=laser_l_delay,
                                                    pulsewidth=laser_l_pulse,
                                                    amplitude=max_laser_voltage,
                                                    offset=0)
        # Pre-allocate the waveforms.
        # This could be improved: create a list with as many zero arrays as analog out lines for ETL and Lasers
        self.identify_laser_idx()
        self.laser_waveform_list = [np.zeros((self.samples)) for i in self.model.DAQParameters.number_of_lasers]
        self.laser_waveform_list[self.laser_idx] = self.laser_template_waveform
        self.laser_do_waveforms = np.stack(self.laser_waveform_list)

    def bundle_galvo_and_etl_waveforms(self):
        '''
        # Stacks the Galvo and ETL waveforms into a numpy array adequate for
        # the NI cards. In here, the assignment of output channels of the Galvo / ETL card to the
        # corresponding output channel is hardcoded: This could be improved.
        '''
        self.galvo_and_etl_waveforms = np.stack((self.galvo_l_waveform,
                                                 self.galvo_r_waveform,
                                                 self.etl_l_waveform))

    def update_etl_parameters(self):
        '''
        # Update the ETL parameters according to the zoom and excitation wavelength.
        '''
        laser = self.model.experiment.current_laser
        zoom = self.model.experiment.zoom
        self.etl_amplitude = self.etl_constants[zoom][laser]['amplitude']
        self.etl_offset = self.etl_constants[zoom][laser]['offset']
        # TODO: Need some sort of system here...

    def create_camera_task(self):
        '''
        # Set up the camera trigger
        # Calculate camera high time and initial delay.
        # Disadvantage: high time and delay can only be set after a task has been created
        '''

        self.camera_trigger_task = nidaqmx.Task()
        camera_delay_percent = self.model.configuration.StartupParameters.camera_delay_percent
        camera_pulse_percent = self.model.configuration.StartupParameters.camera_pulse_percent
        self.camera_high_time = camera_pulse_percent * 0.01 * sweeptime
        self.camera_delay = camera_delay_percent * 0.01 * self.sweeptime
        camera_trigger_out_line = self.model.configuration.DAQParameters['camera_trigger_out_line']
        self.camera_trigger_task.co_channels.add_co_pulse_chan_time(camera_trigger_out_line,
                                                                    high_time=self.camera_high_time,
                                                                    initial_delay=self.camera_delay)
        trigger_source = self.model.configuration.DAQParameters['trigger_source']
        self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source)

    def create_master_trigger_task(self):
        '''
        # Set up the DO master trigger task
        '''
        self.master_trigger_task = nidaqmx.Task()
        master_trigger_out_line = self.model.configuration.DAQParameters['master_trigger_out_line']
        self.master_trigger_task.do_channels.add_do_chan(master_trigger_out_line,
                                                         line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)

    def create_galvo_etl_task(self):
        '''
        # Set up the Galvo and electrotunable lens - Each start with the trigger_source.
        '''
        self.galvo_etl_task = nidaqmx.Task()
        galvo_etl_task_line = self.model.configuration.DAQParameters['galvo_etl_task_line']
        self.galvo_etl_task.ao_channels.add_ao_voltage_chan(galvo_etl_task_line)
        self.galvo_etl_task.timing.cfg_samp_clk_timing(rate=samplerate,
                                                       sample_mode=AcquisitionType.FINITE,
                                                       samps_per_chan=self.samples)
        self.galvo_etl_task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source)

    def create_laser_task(self):
        '''
        # Set up the lasers - Each start with the trigger_source.
        '''
        self.laser_task = nidaqmx.Task()
        laser_task_line = self.model.configuration.DAQParameters['laser_task_line']
        self.laser_task.ao_channels.add_ao_voltage_chan(laser_task_line)
        self.laser_task.timing.cfg_samp_clk_timing(rate=self.samplerate,
                                                   sample_mode=AcquisitionType.FINITE,
                                                   samps_per_chan=samples)
        self.laser_task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source)

    def create_tasks(self):
        '''
        # Creates a total of four tasks for the microscope:
        # These are:
        # - the master trigger task, a digital out task that only provides a trigger pulse for the others
        # - the camera trigger task, a counter task that triggers the camera in lightsheet mode
        # - the galvo task (analog out) that controls the left & right galvos for creation of
        #  the light-sheet and shadow avoidance
        # - the ETL & Laser task (analog out) that controls all the laser intensities (Laser should only
        # be on when the camera is acquiring) and the left/right ETL waveforms
        '''

        # Create the master trigger, camera trigger, etl, and laser tasks
        self.calculate_samples()
        self.create_camera_task()
        self.create_master_trigger_task()
        self.create_galvo_etl_task()
        self.create_laser_task()

    def write_waveforms_to_tasks(self):
        '''
        # Write the waveforms to the slave tasks
        '''
        self.galvo_etl_task.write(self.galvo_and_etl_waveforms)
        self.laser_task.write(self.laser_ao_waveforms)

    def start_tasks(self):
        '''
        # Start the tasks for camera triggering and analog outputs
        # If the tasks are configured to be triggered, they won't output any signals until run_tasks() is called.
        '''
        self.camera_trigger_task.start()
        self.galvo_etl_task.start()
        self.laser_task.start()

    def run_tasks(self):
        '''
        # Run the tasks for triggering, analog and counter outputs.
        # the master trigger initiates all other tasks via a shared trigger
        # For this to work, all analog output and counter tasks have to be started so
        # that they are waiting for the trigger signal.
        '''

        self.master_trigger_task.write([False, True, True, True, False], auto_start=True)
        self.galvo_etl_task.wait_until_done()
        self.laser_task.wait_until_done()
        self.camera_trigger_task.wait_until_done()

    def stop_tasks(self):
        '''
        # Stop the tasks for triggering, analog and counter outputs.
        '''
        self.galvo_etl_task.stop()
        self.laser_task.stop()
        self.camera_trigger_task.stop()
        self.master_trigger_task.stop()

    def close_tasks(self):
        '''
        # Close the tasks for triggering, analog, and counter outputs.
        '''
        self.galvo_etl_task.close()
        self.laser_task.close()
        self.camera_trigger_task.close()
        self.master_trigger_task.close()


if (__name__ == "__main__"):
    print("Testing Mode - WaveFormGenerator Class")
