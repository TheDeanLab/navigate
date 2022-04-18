"""
Triggering for shutters delivered from DAQ using digital outputs.
Each output keeps their last digital state for as long the device is not powered down.

https://nidaqmx-python.readthedocs.io/en/latest/do_channel_collection.html#nidaqmx._task_modules.do_channel_collection.DOChannelCollection
"""

import nidaqmx
from nidaqmx.constants import LineGrouping


class ShutterBase:
    """
    Parent Shutter Class
    """

    def __init__(self, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.verbose = verbose

        # Right Shutter - High Resolution Mode
        self.shutter_right = self.model.DAQParameters['shutter_right']
        self.shutter_right_state = False

        # Left Shutter - Low Resolution Mode
        self.shutter_left = self.model.DAQParameters['shutter_left']
        self.shutter_left_state = False

    def __del__(self):
        pass

    def open_left(self):
        pass

    def open_right(self):
        pass

    def close_shutters(self):
        pass

    def state(self):
        pass


class SyntheticShutter(ShutterBase):
    """
    Virtual Shutter Device
    """

    def __init__(self, model, experiment, verbose=False):
        super().__init__(model, experiment, verbose)

    def open_left(self):
        self.shutter_right_state = False
        self.shutter_left_state = True
        if self.verbose:
            print('Shutter left opened')

    def open_right(self):
        self.shutter_right_state = True
        self.shutter_left_state = False
        if self.verbose:
            print('Shutter right opened')

    def close_shutters(self):
        self.shutter_right_state = False
        self.shutter_left_state = False
        if self.verbose:
            print('Both shutters closed')

    def state(self):
        return self.shutter_left_state, self.shutter_right_state


class ThorlabsShutter(ShutterBase):
    """
    Triggers Thorlabs-based shutter device using National Instruments DAQ
    Requires 5V signal for triggering
    https://www.thorlabs.com/thorproduct.cfm?partnumber=SHB1#ad-image-0
    """

    def __init__(self, model, experiment, verbose=False):
        super().__init__(model, experiment, verbose)

        # Right Shutter - High Resolution Mode
        self.shutter_right_task = nidaqmx.Task()
        self.shutter_right_task.do_channels.add_do_chan(
            self.shutter_right, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.shutter_right_task.write(
            self.shutter_right_state, auto_start=True)

        # Left Shutter - Low Resolution Mode
        self.shutter_left_task = nidaqmx.Task()
        self.shutter_left_task.do_channels.add_do_chan(
            self.shutter_left, line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

    def __del__(self):
        """
        Closes the NI DAQ tasks.
        """
        self.shutter_right_task.close()
        self.shutter_left_task.close()

    def open_left(self):
        """
        Opens the Left Shutter
        Closes the Right Shutter
        """
        self.shutter_right_state = False
        self.shutter_right_task.write(
            self.shutter_right_state, auto_start=True)

        self.shutter_left_state = True
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

        if self.verbose:
            print('Shutter left opened')

    def open_right(self):
        """
        Opens the Right Shutter
        Closes the Left Shutter
        """
        self.shutter_right_state = True
        self.shutter_right_task.write(
            self.shutter_right_state, auto_start=True)

        self.shutter_left_state = False
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

        if self.verbose:
            print('Shutter left opened')

    def close_shutters(self):
        """
        Closes both Shutters
        """
        self.shutter_right_state = False
        self.shutter_right_task.write(
            self.shutter_right_state, auto_start=True)

        self.shutter_left_state = False
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

        if self.verbose:
            print('Both shutters closed')

    def state(self):
        """
        Returns the state of the shutters
        """
        return self.shutter_left_state, self.shutter_right_state
