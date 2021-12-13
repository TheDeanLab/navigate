"""
DAQBase Class

DAQ class with the skeleton functions. Important to keep track of the methods that are
exposed to the View. The class cameraBase should be subclassed when developing new Models.
This ensures that all the methods are automatically inherited and there is no breaks downstream.

**IMPORTANT** Whatever new function is implemented in a specific model,
it should be first declared in the cameraBase class.
In this way the other models will have access to the method and the
program will keep running (perhaps with non intended behavior though).

Adopted and modified from mesoSPIM

"""

class DAQBase():
    def __init__(self, session, verbose):

    def create_tasks(self):
        """"
        Demo version of the actual DAQmx-based function.
        """
        self.calculate_samples()
        #samplerate, sweeptime = self.state.get_parameter_list(['samplerate','sweeptime'])
        #camera_pulse_percent, camera_delay_percent = self.state.get_parameter_list(['camera_pulse_%','camera_delay_%'])
        #self.camera_high_time = camera_pulse_percent*0.01*sweeptime
        #self.camera_delay = camera_delay_percent*0.01*sweeptime

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
        time.sleep(self.state['sweeptime'])

    def stop_tasks(self):
        """"
        Demo: stop tasks
        """
        pass

    def close_tasks(self):
        """
        Demo: closes the tasks for triggering, analog and counter outputs.
        """
        pass