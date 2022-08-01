from pathlib import Path
from aslm.model.aslm_model_config import Configurator
from aslm.model.aslm_model import Model

def get_dummy_model():
    """
    Creates a dummy model to be used for testing. All hardware is synthetic and the current config settings are loaded.
    """
    # Set up the model, experiment, ETL dictionaries
    base_directory = Path(__file__).resolve().parent.parent
    configuration_directory = Path.joinpath(base_directory, 'config')


    config = Path.joinpath(configuration_directory, 'configuration.yml')
    experiment = Path.joinpath(configuration_directory, 'experiment.yml')
    etl_constants = Path.joinpath(configuration_directory, 'etl_constants.yml')

    class args():
        """
        Leaving this class here in case we need to instantiate a full synthetic model
        """
        def __init__(self):
            self.synthetic_hardware = True

    # This return is used when you want a full syntethic model instead of just variable data from config files
    # return Model(False, args(), config, experiment, etl_constants)
    
    class dummy_model():
        def __init__(self):
            self.configuration = Configurator(config)
            self.experiment = Configurator(experiment)
            self.etl_constants = Configurator(etl_constants)
            self.data_buffer = None

    # Instantiate fake model to return
    dumb_model = dummy_model()

    
    return dumb_model
