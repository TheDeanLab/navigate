# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
import os
import sys
import shutil
import platform
from pathlib import Path
from os.path import isfile
from multiprocessing import Manager

# Third Party Imports
import yaml

# Local Imports


def get_aslm_path():
    """Establish a program home directory in AppData/Local/.ASLM for Windows
    or ~/.ASLM for Mac and Linux.

    Returns
    -------
    str
        Path to ASLM home directory.
    """
    if platform.system() == "Windows":
        base_directory = os.getenv("LOCALAPPDATA")
    else:
        base_directory = os.getenv("HOME")
    return os.path.join(base_directory, ".ASLM")


def get_configuration_paths():
    """Get the paths of the various configuration files used by ASLM.

    Returns
    --------
    configuration_path : str
        Path to file containing global microscope configuration,
        i.e. hardware setup
    experiment_path : str
        Path to file containing per-experiment parameters
    etl_constants_path : str
        Path to file containing remote focus parameters for all magnifications
    rest_api_path : str
        Path to file containing REST API configuration
    """
    aslm_directory = get_aslm_path()
    if not os.path.exists(aslm_directory):
        os.mkdir(aslm_directory)
    configuration_directory = Path(os.path.join(aslm_directory, "config"))
    if not os.path.exists(configuration_directory):
        os.mkdir(configuration_directory)

    # Configuration files should be stored in this directory
    configuration_path = Path.joinpath(configuration_directory, "configuration_old.yaml")
    experiment_path = Path.joinpath(configuration_directory, "experiment.yml")
    etl_constants_path = Path.joinpath(configuration_directory, "etl_constants.yml")
    rest_api_path = Path.joinpath(configuration_directory, "rest_api_config.yml")

    # If they are not already, copy the default ones that ship with the software too this folder
    if not os.path.exists(configuration_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_configuration_path = Path.joinpath(
            copy_base_directory, "configuration.yaml"
        )
        shutil.copyfile(copy_configuration_path, configuration_path)

    if not os.path.exists(experiment_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_experiment_path = Path.joinpath(copy_base_directory, "experiment.yml")
        shutil.copyfile(copy_experiment_path, experiment_path)

    if not os.path.exists(etl_constants_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_etl_constants_path = Path.joinpath(
            copy_base_directory, "etl_constants.yml"
        )
        shutil.copyfile(copy_etl_constants_path, etl_constants_path)

    if not os.path.exists(rest_api_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_rest_api_path = Path.joinpath(copy_base_directory, "rest_api_config.yml")
        shutil.copyfile(copy_rest_api_path, rest_api_path)

    return configuration_path, experiment_path, etl_constants_path, rest_api_path


def load_configs(manager, **kwargs):
    """
    Load configuration files.

    Parameters
    ----------
    manager : multiprocessing.Manager
        Shares objects (e.g., dict) between processes
    **kwargs
        List of configuration file paths

    Returns
    -------
    config_dict : dict
        Shared ditionary containing amalgamation of input configurations.
    """
    if kwargs == {}:
        print("No files provided to load_yaml_config()")
        sys.exit(1)

    config_dict = manager.dict()
    for config_name, file_path in kwargs.items():
        file_path = Path(file_path)
        assert file_path.exists(), "Configuration File not found: {}".format(file_path)
        with open(file_path) as f:
            try:
                config_data = yaml.load(f, Loader=yaml.FullLoader)
                build_nested_dict(manager, config_dict, config_name, config_data)
            except yaml.YAMLError as yaml_error:
                print(f"Configuration - Yaml Error: {yaml_error}")
                sys.exit(1)

    # return combined dictionary
    return config_dict


def build_nested_dict(manager, parent_dict, key_name, dict_data):
    """Nest dictionaries recursively.

    Parameters
    ----------
    manager : multiprocessing.Manager
        Shares objects (e.g., dict) between processes
    parent_dict : dict
        Dictionary we are adding to
    key_name : str
        Name of dictionary to insert
    dict_data : dict
        Dictionary to insert

    Returns
    -------
    parent_dict : dict
        Dictionary with subdictionary inserted
    """
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
    """Read a new file and update info of the configuration dict.

    Parameters
    ----------
    manager : multiprocessing.Manager
        Shares objects (e.g., dict) between processes
    parent_dict : dict
        Dictionary we are adding to
    config_name : str
        Name of subdictionary to replace
    new_config : dict
        Dictionary values

    Returns
    -------
    dict
        Dictionary with replaced sub dictionary
    """
    if type(new_config) != dict:
        file_path = str(new_config)
        if isfile(file_path) and (
            file_path.endswith(".yml") or file_path.endswith(".yaml")
        ):
            with open(file_path) as f:
                new_config = yaml.load(f, Loader=yaml.FullLoader)
        else:
            return False

    build_nested_dict(manager, parent_dict, config_name, new_config)
