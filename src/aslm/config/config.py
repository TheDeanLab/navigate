import os
import shutil
import platform
from pathlib import Path

def get_configuration_paths():
    # Establish a base directory in AppData/Local/.ASLM for Windows or ~/.ASLM for Mac and Linux
    if platform.system() == 'Windows':
        base_directory = os.getenv('LOCALAPPDATA')
    else:
        base_directory = os.getenv('HOME')
    aslm_directory = os.path.join(base_directory, '.ASLM')
    if not os.path.exists(aslm_directory):
        os.mkdir(aslm_directory)
    configuration_directory = Path(os.path.join(aslm_directory, 'config'))
    if not os.path.exists(configuration_directory):
        os.mkdir(configuration_directory)

    # Configuration files should be stored in this directory
    configuration_path = Path.joinpath(configuration_directory, 'configuration.yml')
    experiment_path = Path.joinpath(configuration_directory, 'experiment.yml')
    etl_constants_path = Path.joinpath(configuration_directory, 'etl_constants.yml')

    # If they are not already, copy the default ones that ship with the software too this folder
    if not os.path.exists(configuration_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_configuration_path = Path.joinpath(copy_base_directory, 'configuration.yml')
        shutil.copyfile(copy_configuration_path, configuration_path)

    if not os.path.exists(experiment_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_experiment_path = Path.joinpath(copy_base_directory, 'experiment.yml')
        shutil.copyfile(copy_experiment_path, experiment_path)

    if not os.path.exists(etl_constants_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_etl_constants_path = Path.joinpath(copy_base_directory, 'etl_constants.yml')
        shutil.copyfile(copy_etl_constants_path, etl_constants_path)
    
    return configuration_path, experiment_path, etl_constants_path
