class ShutterBase:
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
