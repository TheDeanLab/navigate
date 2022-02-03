import nidaqmx
from nidaqmx.constants import LineGrouping


class NIShutter:
    """
    Slow shutter, intended more as a gating device than a fast open/close because the
    NI task is recreated and deleted every time a shutter is actuated.

    Thus, the shutter has more a "gating" function to protect the sample than
    fast control of the laser, this is done via the laser intensity anyway.

    This uses the property of NI-DAQmx-outputs to keep their last digital state or
    analog voltage for as long the device is not powered down.

    https://nidaqmx-python.readthedocs.io/en/latest/do_channel_collection.html#nidaqmx._task_modules.do_channel_collection.DOChannelCollection
    """
    def __init__(self, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.verbose = verbose

        # Right Shutter - High Resolution Mode
        self.shutter_right = self.model.DAQParameters['shutter_right']
        self.shutter_right_state = False
        self.shutter_right_task = nidaqmx.Task()
        self.shutter_right_task.do_channels.add_do_chan(self.shutter_right,
                                                        line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.shutter_right_task.write(self.shutter_right_state, auto_start=True)

        # Left Shutter - Low Resolution Mode
        self.shutter_left = self.model.DAQParameters['shutter_left']
        self.shutter_left_state = False
        self.shutter_left_task = nidaqmx.Task()
        self.shutter_left_task.do_channels.add_do_chan(self.shutter_left,
                                                        line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

    def __del__(self):
        self.shutter_right_task.close()
        self.shutter_left_task.close()

    def open_left(self, *args):
        self.shutter_right_state = False
        self.shutter_right_task.write(self.shutter_right_state, auto_start=True)

        self.shutter_left_state = True
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

        if self.verbose:
            print('Shutter left opened')

    def open_right(self, *args):
        self.shutter_right_state = True
        self.shutter_right_task.write(self.shutter_right_state, auto_start=True)

        self.shutter_left_state = False
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

        if self.verbose:
            print('Shutter left opened')

    def close_shutters(self, *args):
        self.shutter_right_state = False
        self.shutter_right_task.write(self.shutter_right_state, auto_start=True)

        self.shutter_left_state = False
        self.shutter_left_task.write(self.shutter_left_state, auto_start=True)

        if self.verbose:
            print('Both shutters closed')

    def state(self, *args):
        return self.shutter_left_state, self.shutter_right_state