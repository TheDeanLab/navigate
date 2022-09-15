import os
import sys
import shutil
import platform
from pathlib import Path
from os.path import isfile
from multiprocessing import Manager

import yaml

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
    configuration_path = Path.joinpath(configuration_directory, 'configuration.yaml')
    experiment_path = Path.joinpath(configuration_directory, 'experiment.yml')
    etl_constants_path = Path.joinpath(configuration_directory, 'etl_constants.yml')

    # If they are not already, copy the default ones that ship with the software too this folder
    if not os.path.exists(configuration_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_configuration_path = Path.joinpath(copy_base_directory, 'configuration.yaml')
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

def load_configs(manager, **kwargs):
    if kwargs == {}:
        print("No files provided to load_yaml_config()")
        sys.exit(1)

    config_dict = manager.dict()
    for config_name, file_path in kwargs.items():
        file_path = Path(file_path)
        assert file_path.exists(), 'Configuration File not found: {}'.format(file_path)
        with open(file_path) as f:
            try:
                config_data = yaml.load(f, Loader=yaml.FullLoader)
                build_nested_dict(manager, config_dict, config_name, config_data)
            except yaml.YAMLError as yaml_error:
                print(f"Configurator - Yaml Error: {yaml_error}")
                sys.exit(1)
    
    # return combined dictionary
    return config_dict

def build_nested_dict(manager, parent_dict, key_name, dict_data):
    if type(dict_data) != dict and type(dict_data) != list:
        parent_dict[key_name] = dict_data
        return
    if type(dict_data) == dict:
        d = manager.dict()
        for k in dict_data:
            build_nested_dict(manager, d, k, dict_data[k])
    else:
        d = manager.list()
        for i, v in enumerate(dict_data):
            d.append(None)
            build_nested_dict(manager, d, i, v)
    parent_dict[key_name] = d

def update_config_dict(manager, parent_dict, config_name, new_config) -> bool:
    if type(new_config) != dict:
        file_path = str(new_config)
        if isfile(file_path) and (file_path.ends('.yml') or file_path.ends('.yaml')):
            with open(file_path) as f:
                new_config = yaml.load(f, Loader=yaml.FullLoader)
        else:
            return False
    
    build_nested_dict(manager, parent_dict, config_name, new_config)
