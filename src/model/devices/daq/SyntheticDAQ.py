"""
NI Synthetic DAQ Class
"""

# Standard Imports

# Local Imports
from model.aslm_model_waveforms import tunable_lens_ramp, sawtooth, dc_value, single_pulse
from .DAQBase import DAQBase as DAQBase

class DAQ(DAQBase):
    def __init__(self, model, experiment, etl_constants, verbose=False):
        self.model = model
        self.experiment = experiment
        self.etl_constants = etl_constants
        self.verbose = verbose

        # Initialize Variables
        self.sample_rate = self.model.DAQParameters['sample_rate']
        self.sweep_time = self.model.DAQParameters['sweep_time']
        self.samples = int(self.sample_rate * self.sweep_time)

        # ETL Parameters
        self.etl_l_waveform = None
        self.etl_l_delay = self.model.RemoteFocusParameters['remote_focus_l_delay_percent']
        self.etl_l_ramp_rising = self.model.RemoteFocusParameters['remote_focus_l_ramp_rising_percent']
        self.etl_l_ramp_falling = self.model.RemoteFocusParameters['remote_focus_l_ramp_falling_percent']
        self.etl_l_amplitude = self.model.RemoteFocusParameters['remote_focus_l_amplitude']
        self.etl_l_offset = self.model.RemoteFocusParameters['remote_focus_l_offset']
        self.etl_l_min_ao = self.model.RemoteFocusParameters['remote_focus_l_min_ao']
        self.etl_l_max_ao = self.model.RemoteFocusParameters['remote_focus_l_max_ao']

        # Remote Focus Parameters
        self.etl_r_waveform = None
        self.etl_r_delay = self.model.RemoteFocusParameters['remote_focus_r_delay_percent']
        self.etl_r_ramp_rising = self.model.RemoteFocusParameters['remote_focus_r_ramp_rising_percent']
        self.etl_r_ramp_falling = self.model.RemoteFocusParameters['remote_focus_r_ramp_falling_percent']
        self.etl_r_amplitude = self.model.RemoteFocusParameters['remote_focus_r_amplitude']
        self.etl_r_offset = self.model.RemoteFocusParameters['remote_focus_r_offset']
        self.etl_r_min_ao = self.model.RemoteFocusParameters['remote_focus_r_min_ao']
        self.etl_r_max_ao = self.model.RemoteFocusParameters['remote_focus_r_max_ao']

        # Left Galvo Parameters
        self.galvo_l_waveform = None
        self.galvo_and_etl_waveforms = None
        self.galvo_l_frequency = self.model.GalvoParameters['galvo_l_frequency']
        self.galvo_l_amplitude = self.model.GalvoParameters['galvo_l_amplitude']
        self.galvo_l_offset = self.model.GalvoParameters['galvo_l_offset']
        self.galvo_l_duty_cycle = self.model.GalvoParameters['galvo_l_duty_cycle']
        self.galvo_l_phase = self.model.GalvoParameters['galvo_l_phase']
        self.galvo_l_min_ao = self.model.GalvoParameters['galvo_l_min_ao']

        # Right Galvo Parameters
        self.galvo_r_max_ao = self.model.GalvoParameters['galvo_l_max_ao']
        self.galvo_r_amplitude = self.model.GalvoParameters['galvo_r_amplitude']
        self.galvo_r_min_ao = self.model.GalvoParameters['galvo_r_min_ao']
        self.galvo_r_max_ao = self.model.GalvoParameters['galvo_r_max_ao']
        self.galvo_r_waveform = None

        # Camera Parameters
        self.camera_delay_percent = self.model.CameraParameters['delay_percent']
        self.camera_pulse_percent = self.model.CameraParameters['pulse_percent']
        self.camera_high_time = self.camera_pulse_percent * 0.01 * self.sweep_time
        self.camera_delay = self.camera_delay_percent * 0.01 * self.sweep_time

        # Laser Parameters
        self.laser_idx = None
        self.laser_switching_waveform = None
        self.laser_ao_waveforms = None
        self.laser_do_waveforms = None
        self.number_of_lasers = self.model.LaserParameters['number_of_lasers']
        self.laser_l_delay = self.model.LaserParameters['laser_l_delay_percent']
        self.laser_l_pulse = self.model.LaserParameters['laser_l_pulse_percent']
        self.laser_min_ao = self.model.LaserParameters['laser_min_ao']
        self.laser_max_ao = self.model.LaserParameters['laser_max_ao']
        self.laser_min_do = self.model.LaserParameters['laser_min_do']
        self.laser_max_do = self.model.LaserParameters['laser_max_do']
        self.fiber_idx = self.experiment.MicroscopeState['fiber']
        self.laser_power = 0

    def calculate_samples(self):
        """
        # Calculate the number of samples for the waveforms.
        # Product of the sampling frequency and the duration of the waveform.
        """
        self.sample_rate = self.model.DAQParameters['sample_rate']
        self.sweep_time = self.model.DAQParameters['sweep_time']
        self.samples = int(self.sample_rate * self.sweep_time)
        if self.verbose:
            print('Number of samples: ' + str(self.samples))

    def create_waveforms(self):
        """
        # Create the waveforms for the ETL, Galvos, and Lasers.
        """
        self.calculate_samples()

        # ETL - Currently creates both ETL L and ETL R
        self.create_etl_waveform()

        # Galvos
        self.create_high_res_galvo_waveform()
        self.create_low_res_galvo_waveform()

        # Lasers
        self.create_analog_laser_waveforms(self.laser_power)
        self.create_digital_laser_waveforms()
        self.create_laser_switching_waveform()

        # Bundle the waveforms into a single waveform.
        self.bundle_galvo_and_etl_waveforms()

    def create_etl_waveform(self):
        """
        # Create the waveforms for the Electrotunable Lens
        """
        self.calculate_samples()
        self.etl_l_waveform = tunable_lens_ramp(self.sample_rate, self.sweep_time, self.etl_l_delay,
                                                self.etl_l_ramp_rising, self.etl_l_ramp_falling,
                                                self.etl_l_amplitude, self.etl_l_offset)

        self.etl_r_waveform = tunable_lens_ramp(self.sample_rate, self.sweep_time, self.etl_r_delay,
                                                self.etl_r_ramp_rising, self.etl_r_ramp_falling,
                                                self.etl_r_amplitude, self.etl_r_offset)
        # Scale the ETL waveforms to the AO range.
        self.etl_l_waveform[self.etl_l_waveform < self.etl_l_min_ao] = self.etl_l_min_ao
        self.etl_l_waveform[self.etl_l_waveform > self.etl_l_max_ao] = self.etl_l_max_ao
        self.etl_r_waveform[self.etl_r_waveform < self.etl_r_min_ao] = self.etl_r_min_ao
        self.etl_r_waveform[self.etl_r_waveform > self.etl_r_max_ao] = self.etl_r_max_ao

    def create_low_res_galvo_waveform(self):
        """
        # Calculate the sawtooth waveforms for the low-resolution digitally scanned galvo.
        """
        self.calculate_samples()
        self.galvo_l_waveform = sawtooth(self.sample_rate, self.sweep_time, self.galvo_l_frequency,
                                         self.galvo_l_amplitude, self.galvo_l_offset,
                                         self.galvo_l_duty_cycle, self.galvo_l_phase)

        # Scale the Galvo waveforms to the AO range.
        self.galvo_l_waveform[self.galvo_l_waveform < self.galvo_l_min_ao] = self.galvo_l_min_ao
        self.galvo_l_waveform[self.galvo_l_waveform > self.galvo_r_max_ao] = self.galvo_r_max_ao

    def create_high_res_galvo_waveform(self):
        """
        # Calculate the DC waveform for the resonant galvanometer drive signal.
        """
        self.calculate_samples()
        self.galvo_r_waveform = dc_value(self.sample_rate, self.sweep_time, self.galvo_r_amplitude, 0)

        # Scale the Galvo waveforms to the AO range.
        self.galvo_r_waveform[self.galvo_r_waveform < self.galvo_r_min_ao] = self.galvo_r_min_ao
        self.galvo_r_waveform[self.galvo_r_waveform > self.galvo_r_max_ao] = self.galvo_r_max_ao

    def identify_laser_idx(self, laser_wavelength):
        """
        # TODO: Make this so that it automatically grows with the number of lasers in the model
        """
        for laser_idx in range(self.number_of_lasers):
            if laser_wavelength == self.model.LaserParameters['laser_0_wavelength']:
                self.laser_idx = self.model.LaserParameters['laser_0_index']
            elif laser_wavelength == self.model.LaserParameters['laser_1_wavelength']:
                self.laser_idx = self.model.LaserParameters['laser_1_index']
            elif laser_wavelength == self.model.LaserParameters['laser_2_wavelength']:
                self.laser_idx = self.model.LaserParameters['laser_2_index']
            else:
                print('Laser name not found.')
            if self.verbose:
                print('Laser index: {}'.format(self.laser_idx))

    def create_laser_switching_waveform(self):
        """
        # TTL for switching between laser fibers.
        # 0V is the left fiber, 5V is the right.
        """
        self.calculate_samples()
        if self.fiber_idx == 0:
            amplitude = self.model.LaserParameters['laser_min_do']
        else:
            amplitude = self.model.LaserParameters['laser_max_do']
        self.laser_switching_waveform = dc_value(self.sample_rate, self.sweep_time, amplitude, 0)

    def create_analog_laser_waveforms(self, laser_power):
        """
        # Calculate the waveforms for the lasers.
        # Analog output for intensity control
        # Digital output for left or right fiber.
        """
        self.calculate_samples()
        laser_voltage = self.laser_max_ao * laser_power / 100
        laser_template_waveform = single_pulse(self.sample_rate, self.sweep_time, self.laser_l_delay,
                                               self.laser_l_pulse, laser_voltage, 0)

        # Scale the waveforms to the AO range.
        laser_template_waveform[laser_template_waveform < self.laser_min_ao] = self.laser_min_ao
        laser_template_waveform[laser_template_waveform > self.laser_max_ao] = self.laser_max_ao

        # Pre-allocate the waveforms.
        laser_waveform_list = [np.zeros(self.samples) for i in range(self.number_of_lasers)]
        laser_waveform_list[self.laser_idx] = laser_template_waveform
        self.laser_ao_waveforms = np.stack(laser_waveform_list)

    def create_digital_laser_waveforms(self):
        """
        # Calculate the waveforms for the lasers.
        # Digital output for on/off.
        # Digital output for left or right fiber.
        """
        self.calculate_samples()
        laser_template_waveform = single_pulse(self.sample_rate, self.sweep_time, self.laser_l_delay,
                                               self.laser_l_pulse, self.laser_max_do, 0)

        # Scale the waveforms to the DO range.
        laser_template_waveform[laser_template_waveform < self.laser_min_do] = self.laser_min_do
        laser_template_waveform[laser_template_waveform > self.laser_max_do] = self.laser_max_do

        # Pre-allocate the waveforms.
        laser_waveform_list = [np.zeros(self.samples) for i in range(self.number_of_lasers)]
        laser_waveform_list[self.laser_idx] = laser_template_waveform
        self.laser_do_waveforms = np.stack(laser_waveform_list)

    def bundle_galvo_and_etl_waveforms(self):
        """
        # Stacks the Galvo and ETL waveforms into a numpy array adequate for
        # the NI cards. In here, the assignment of output channels of the Galvo / ETL card to the
        # corresponding output channel is hardcoded: This could be improved.
        """
        self.galvo_and_etl_waveforms = np.stack((self.galvo_l_waveform,
                                                 self.galvo_r_waveform,
                                                 self.etl_l_waveform,
                                                 self.etl_r_waveform))

    def update_etl_parameters(self):
        """
        # Update the ETL parameters according to the zoom and excitation wavelength.
        # TODO: Need some sort of system here...
        """
        #  laser = self.model.experiment.current_laser
        #  zoom = self.model.experiment.zoom
        #  self.etl_amplitude = self.etl_constants[zoom][laser]['amplitude']
        #  self.etl_offset = self.etl_constants[zoom][laser]['offset']
        pass

    def create_camera_task(self):
        """
        # Set up the camera trigger
        # Calculate camera high time and initial delay.
        # Disadvantage: high time and delay can only be set after a task has been created
        """
        # Configure camera triggers
        camera_trigger_out_line = self.model.DAQParameters['camera_trigger_out_line']
        pass

    def create_master_trigger_task(self):
        """
        # Set up the DO master trigger task
        """
        master_trigger_out_line = self.model.DAQParameters['master_trigger_out_line']
        pass

    def create_galvo_etl_task(self):
        """
        # Set up the Galvo and electrotunable lens - Each start with the trigger_source.
        """
        trigger_source = self.model.DAQParameters['trigger_source']
        pass

    def create_laser_task(self):
        """
        # Set up the lasers - Each start with the trigger_source.
        """
        trigger_source = self.model.DAQParameters['trigger_source']
        laser_task_line = self.model.DAQParameters['laser_task_line']
        pass

    def create_tasks(self):
        """
        # Creates a total of four tasks for the microscope:
        # These are:
        # - the master trigger task, a digital out task that only provides a trigger pulse for the others
        # - the camera trigger task, a counter task that triggers the camera in lightsheet mode
        # - the galvo task (analog out) that controls the left & right galvos for creation of
        #  the light-sheet and shadow avoidance
        # - the ETL & Laser task (analog out) that controls all the laser intensities (Laser should only
        # be on when the camera is acquiring) and the left/right ETL waveforms
        """
        self.calculate_samples()
        pass

    def write_waveforms_to_tasks(self):
        """
        # Write the waveforms to the slave tasks
        """
        pass

    def start_tasks(self):
        """
        # Start the tasks for camera triggering and analog outputs
        # If the tasks are configured to be triggered, they won't output any signals until run_tasks() is called.
        """
        pass

    def run_tasks(self):
        """
        # Run the tasks for triggering, analog and counter outputs.
        # the master trigger initiates all other tasks via a shared trigger
        # For this to work, all analog output and counter tasks have to be started so
        # that they are waiting for the trigger signal.
        """
        pass

    def stop_tasks(self):
        """
        # Stop the tasks for triggering, analog and counter outputs.
        """
        pass

    def close_tasks(self):
        """
        # Close the tasks for triggering, analog, and counter outputs.
        """
        pass

    def initialize_tasks(self):
        """
        # Initialize the nidaqmx tasks.
        """
        pass