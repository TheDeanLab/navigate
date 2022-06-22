from pathlib import Path
from aslm.model.aslm_model_config import Session as session
from aslm.model.aslm_model import Model

def get_dummy_model():
    '''
    Creates a dummy model to be used for testing. All hardware is synthetic and the current config settings are loaded.
    '''
    # Set up the model, experiment, ETL dictionaries
    base_directory = Path(__file__).resolve().parent.parent.parent.parent
    configuration_directory = Path.joinpath(base_directory, 'src/aslm', 'config')

    config = Path.joinpath(configuration_directory, 'configuration.yml')
    experiment = Path.joinpath(configuration_directory, 'experiment.yml')
    etl_constants = Path.joinpath(configuration_directory, 'etl_constants.yml')

    class args():
        def __init__(self):
            self.verbose = False
            self.synthetic_hardware = True
    
    return Model(False, args(), config, experiment, etl_constants)