from email.mime import base
from pathlib import Path

def test_synthetic_daq():
    from src.model.devices.daq import SyntheticDAQ
    from src.model.aslm_model_config import Session as session

    base_directory = Path(__file__).resolve().parent.parent.parent.parent
    configuration_directory = Path.joinpath(base_directory, 'src', 'config')
    
    model = session(Path.joinpath(configuration_directory, 'configuration.yml'))
    experiment = session(Path.joinpath(configuration_directory, 'experiment.yml'))
    etl_constants = session(Path.joinpath(configuration_directory, 'etl_constants.yml'))

    SyntheticDAQ(model, experiment, etl_constants)

    return True