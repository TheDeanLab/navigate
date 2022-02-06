from model.devices.shutters.ShutterBase import ShutterBase


class DemoShutter(ShutterBase):
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
