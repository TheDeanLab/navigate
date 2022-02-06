import time


class DAQBase:
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
        self.resolution_mode = self.experiment.MicroscopeState['resolution_mode']
        self.laser_power = 0
        self.laser_idx = 0

    def create_tasks(self):
        """
        Demo version of the actual DAQmx-based function.
        """
        pass

    def write_waveforms_to_tasks(self):
        """
        Demo: write the waveforms to the slave tasks
        """
        pass

    def start_tasks(self):
        """
        Demo: starts the tasks for camera triggering and analog outputs.
        """
        pass

    def run_tasks(self):
        """
        Demo: runs the tasks for triggering, analog and counter outputs.
        """
        time.sleep(self.model.sweeptime)

    def stop_tasks(self):
        """
        Demo: stop tasks
        """
        pass

    def close_tasks(self):
        """
        Demo: closes the tasks for triggering, analog and counter outputs.
        """
        pass
