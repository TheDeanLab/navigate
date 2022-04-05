import nidaqmx
from nidaqmx.constants import LineGrouping

class LaserSwitching():
    def __init__(self, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.verbose = verbose

        # Laser Switching DAQ Output
        self.switching_port = self.model.DAQParameters['laser_port_switcher']
        self.switching_state = False

        # Initialize the DAQ Task
        self.switching_task = nidaqmx.Task()
        self.switching_task.do_channels.add_do_chan(self.switching_port,
                                                    line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.switching_task.write(self.switching_state, auto_start=True)

    def __del__(self):
        self.switching_task.close()

    def enable_low_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """

        self.switching_state = False
        self.switching_task.write(self.switching_state, auto_start=True)
        print("Low Resolution Laser Path Enabled")

    def enable_high_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """

        self.switching_state = True
        self.switching_task.write(self.switching_state, auto_start=True)
        print("High Resolution Laser Path Enabled")


class SyntheticLaserSwitching():
    def __init__(self, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.verbose = verbose

        # Laser Switching DAQ Output
        self.switching_port = self.model.DAQParameters['laser_port_switcher']
        self.switching_state = False

    def __del__(self):
        pass

    def enable_low_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """

        self.switching_state = False
        print("Low Resolution Laser Path Enabled")

    def enable_high_resolution_laser(self):
        """
        # Evaluates the experiment configuration in the model for the resolution mode.
        # Triggers the DAQ to select the correct laser path.
        """

        self.switching_state = True
        print("High Resolution Laser Path Enabled")
