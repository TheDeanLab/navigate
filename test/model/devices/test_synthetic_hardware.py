# from email.mime import base
# from pathlib import Path

# from numpy import triu_indices
# from aslm.model.aslm_model_config import Session as session

# Set up the model, experiment, ETL dictionaries
# base_directory = Path(__file__).resolve().parent.parent.parent.parent
# configuration_directory = Path.joinpath(base_directory, 'src/aslm', 'config')

# model = session(Path.joinpath(configuration_directory, 'configuration.yml'))
# experiment = session(Path.joinpath(configuration_directory, 'experiment.yml'))
# etl_constants = session(Path.joinpath(configuration_directory, 'etl_constants.yml'))
from aslm.model.dummy_model import get_dummy_model

class TestSyntheticHardware():
        
        
    def test_synthetic_daq(self):
        from aslm.model.devices.daq import SyntheticDAQ
        self.dummy_model = get_dummy_model()
        self.config = self.dummy_model.configuration
        self.experiment = self.dummy_model.experiment
        self.etl_const = self.dummy_model.etl_constants
        self.verbose = self.dummy_model.verbose

        
        sd = SyntheticDAQ(self.config, self.experiment, self.etl_const, self.verbose)

        assert True



    def test_synthetic_camera(self):
        from aslm.model.devices.cameras import SyntheticCamera
        self.dummy_model = get_dummy_model()
        self.config = self.dummy_model.configuration
        self.experiment = self.dummy_model.experiment
        self.etl_const = self.dummy_model.etl_constants
        self.verbose = self.dummy_model.verbose


        sc = SyntheticCamera(0, self.config, self.experiment)

        return True

    def test_synthetic_filter_wheel(self):
        from aslm.model.devices.filter_wheels import SyntheticFilterWheel
        self.dummy_model = get_dummy_model()
        self.config = self.dummy_model.configuration
        self.experiment = self.dummy_model.experiment
        self.etl_const = self.dummy_model.etl_constants
        self.verbose = self.dummy_model.verbose

        sf = SyntheticFilterWheel(self.config, False)

        return True

    def test_synthetic_stage(self):
        from aslm.model.devices.stages import SyntheticStage
        self.dummy_model = get_dummy_model()
        self.config = self.dummy_model.configuration
        self.experiment = self.dummy_model.experiment
        self.etl_const = self.dummy_model.etl_constants
        self.verbose = self.dummy_model.verbose

        ss = SyntheticStage(self.config, False)

    def test_synthetic_zoom(self):
        from aslm.model.devices.zoom import SyntheticZoom
        self.dummy_model = get_dummy_model()
        self.config = self.dummy_model.configuration
        self.experiment = self.dummy_model.experiment
        self.etl_const = self.dummy_model.etl_constants
        self.verbose = self.dummy_model.verbose

        sz = SyntheticZoom(self.config, False)

        return True

    def test_synthetic_shutter(self):
        from aslm.model.devices.laser_shutters import SyntheticShutter
        self.dummy_model = get_dummy_model()
        self.config = self.dummy_model.configuration
        self.experiment = self.dummy_model.experiment
        self.etl_const = self.dummy_model.etl_constants
        self.verbose = self.dummy_model.verbose

        ss = SyntheticShutter(self.config, self.experiment)

        return True

    def test_synthetic_laser(self):
        from aslm.model.devices.lasers.SyntheticLaser import SyntheticLaser
        self.dummy_model = get_dummy_model()
        self.config = self.dummy_model.configuration
        self.experiment = self.dummy_model.experiment
        self.etl_const = self.dummy_model.etl_constants
        self.verbose = self.dummy_model.verbose

        sl = SyntheticLaser(self.config, False)

        return True
