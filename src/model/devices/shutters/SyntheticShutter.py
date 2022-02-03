class DemoShutter:
    def __init__(self, model, experiment, verbose=False):
        self.model = model
        self.experiment = experiment
        self.verbose = verbose

        self.shutter_right = self.model.DAQParameters['shutter_right']
        self.shutter_left = self.model.DAQParameters['shutter_left']

        self.shutter_right_state = False
        self.shutter_left_state = False

    def open_left(self, *args):
        self.shutter_right_state = False
        self.shutter_left_state = True
        if self.verbose:
            print('Shutter left opened')

    def open_right(self, *args):
        self.shutter_right_state = True
        self.shutter_left_state = False
        if self.verbose:
            print('Shutter right opened')

    def close_shutters(self, *args):
        self.shutter_right_state = False
        self.shutter_left_state = False
        if self.verbose:
            print('Both shutters closed')

    def state(self, *args):
        return self.shutter_left_state, self.shutter_right_state
