from aslm.model.model_features.aslm_feature_container import dummy_True

class ChangeResolution:
    def __init__(self, model, resolution_mode='high'):
        self.model = model

        self.config_table={'signal': {'main': self.signal_func}, 
                            'data': {'main': dummy_True}}

        self.resolution_mode = resolution_mode

        
    def signal_func(self):
        self.model.change_resolution(self.resolution_mode)
        self.model.prepare_acquisition(False)
        return True

    def generate_meta_data(self, *args):
        print('This frame: change resolution', self.resolution_mode, self.model.frame_id)
        return True

class Snap:
    def __init__(self, model):
        self.model = model

        self.config_table={'signal':{},
                            'data': {'main': dummy_True}}

    def generate_meta_data(self, *args):
        print('This frame: snap one frame', self.model.frame_id)
        return True