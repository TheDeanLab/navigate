# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
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
from multiprocessing.managers import ListProxy, DictProxy

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

    Examples
    --------
    >>> get_aslm_path()
    'C:\\Users\\username\\AppData\\Local\\.ASLM'
    """
    if platform.system() == "Windows":
        base_directory = os.getenv("LOCALAPPDATA")
    else:
        base_directory = os.getenv("HOME")
    aslm_path = os.path.join(base_directory, ".ASLM")

    if not os.path.exists(aslm_path):
        os.mkdir(aslm_path)

    return aslm_path


def get_configuration_paths():
    """Get the paths of the various configuration files used by ASLM.

    Returns
    --------
    configuration_path : str
        Path to file containing global microscope configuration,
        i.e. hardware setup
    experiment_path : str
        Path to file containing per-experiment parameters
    waveform_constants_path : str
        Path to file containing remote focus parameters for all magnifications
    rest_api_path : str
        Path to file containing REST API configuration
    waveform_templates_path : str
        Path to file containing waveform templates
    """
    aslm_directory = get_aslm_path()
    if not os.path.exists(aslm_directory):
        os.mkdir(aslm_directory)
    configuration_directory = Path(os.path.join(aslm_directory, "config"))
    if not os.path.exists(configuration_directory):
        os.mkdir(configuration_directory)

    # Configuration files should be stored in this directory
    configuration_path = Path.joinpath(configuration_directory, "configuration.yaml")
    experiment_path = Path.joinpath(configuration_directory, "experiment.yml")
    waveform_constants_path = Path.joinpath(
        configuration_directory, "waveform_constants.yml"
    )
    rest_api_path = Path.joinpath(configuration_directory, "rest_api_config.yml")
    waveform_templates_path = Path.joinpath(
        configuration_directory, "waveform_templates.yml"
    )

    # If they are not already,
    # copy the default ones that ship with the software to this folder
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

    if not os.path.exists(waveform_constants_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_waveform_constants_path = Path.joinpath(
            copy_base_directory, "waveform_constants.yml"
        )
        shutil.copyfile(copy_waveform_constants_path, waveform_constants_path)

    if not os.path.exists(rest_api_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_rest_api_path = Path.joinpath(copy_base_directory, "rest_api_config.yml")
        shutil.copyfile(copy_rest_api_path, rest_api_path)

    if not os.path.exists(waveform_templates_path):
        copy_base_directory = Path(__file__).resolve().parent
        copy_waveform_templates_path = Path.joinpath(
            copy_base_directory, "waveform_templates.yml"
        )
        shutil.copyfile(copy_waveform_templates_path, waveform_templates_path)

    return (
        configuration_path,
        experiment_path,
        waveform_constants_path,
        rest_api_path,
        waveform_templates_path,
    )


def load_configs(manager, **kwargs):
    """Load configuration files.

    Parameters
    ----------
    manager : multiprocessing.Manager
        Shares objects (e.g., dict) between processes
    **kwargs
        List of configuration file paths

    Returns
    -------
    config_dict : dict
        Shared dictionary containing amalgamation of input configurations.
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
    None

    Examples
    --------
    >>> build_nested_dict(manager, parent_dict, key_name, dict_data)
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
    bool
        True or False

    Examples
    --------
    >>> update_config_dict(manager, parent_dict, config_name, new_config)
    """
    if type(new_config) != dict and type(new_config) != list:
        file_path = str(new_config)
        if isfile(file_path) and (
            file_path.endswith(".yml") or file_path.endswith(".yaml")
        ):
            with open(file_path) as f:
                new_config = yaml.load(f, Loader=yaml.FullLoader)
        else:
            return False

    build_nested_dict(manager, parent_dict, config_name, new_config)
    return True


def verify_experiment_config(manager, configuration):
    """Verify configuration (configuration, experiment, waveform_constants) yaml files

    Parameters
    ----------
    manager : multiprocessing.Manager
        Shares objects (e.g., dict) between processes
    configuration: configuration object
        contains all the yaml files
    """
    # verify/build autofocus parameter setting
    # get autofocus supported devices(stages, remote_focus) from configuration.yaml file
    device_dict = {}
    # get devices: stages, NI remote_focus_device
    device_config = configuration["configuration"]["microscopes"]
    for microscope_name in device_config.keys():
        microscope_config = device_config[microscope_name]
        device_dict[microscope_name] = {}
        if "remote_focus_device" in microscope_config.keys() and microscope_config["remote_focus_device"]["hardware"]["type"] == "NI":
            device_dict[microscope_name]["remote_focus"] = {}
            device_ref = microscope_config["remote_focus_device"]["hardware"]["channel"]
            device_dict[microscope_name]["remote_focus"][device_ref] = True
        if "stage" in microscope_config.keys():
            stages = microscope_config["stage"]["hardware"]
            device_dict[microscope_name]["stage"] = {}
            if type(stages) != ListProxy:
                stages = [stages]
            for stage in stages:
                if not stage["type"].lower().startswith("synthetic"):
                    for axis in stage["axes"]:
                        device_dict[microscope_name]["stage"][axis] = True

    autofocus_sample_setting = {
        "coarse_range": 500,
        "coarse_step_size": 50,
        "coarse_selected": True,
        "fine_range": 50,
        "fine_step_size": 5,
        "fine_selected": True,
        "robust_fit": False
    }
    autofocus_setting_dict = configuration["experiment"]["AutoFocusParameters"]
    # verify if all the devices have been added to the autofocus parameter dict
    for microscope_name in device_dict:
        if microscope_name not in autofocus_setting_dict.keys():
            update_config_dict(
                manager,
                autofocus_setting_dict,
                microscope_name,
                {}
            )
        for device in device_dict[microscope_name]:
            if device not in autofocus_setting_dict[microscope_name].keys():
                update_config_dict(
                    manager,
                    autofocus_setting_dict[microscope_name],
                    device,
                    {},
                )
            for device_ref in device_dict[microscope_name][device]:
                if device_ref not in autofocus_setting_dict[microscope_name][device].keys():
                    update_config_dict(
                        manager,
                        autofocus_setting_dict[microscope_name][device],
                        device_ref,
                        autofocus_sample_setting
                    )

    # remove non-consistent autofocus parameter
    for microscope_name in autofocus_setting_dict.keys():
        if microscope_name not in device_dict:
            autofocus_setting_dict.pop(microscope_name)
        else:
            for device in autofocus_setting_dict[microscope_name].keys():
                if device not in device_dict[microscope_name]:
                    autofocus_setting_dict[microscope_name].pop(device)
                else:
                    for device_ref in autofocus_setting_dict[microscope_name][device].keys():
                        if device_ref not in autofocus_setting_dict[microscope_name][device]:
                            autofocus_setting_dict[microscope_name][device].pop(device_ref)

def verify_waveform_constants(manager, configuration):
    if type(configuration["waveform_constants"]) is not DictProxy:
        update_config_dict(
            manager,
            configuration,
            "waveform_constants",
            {}
        )
    waveform_dict = configuration["waveform_constants"]

    # remote_focus_constants
    if "remote_focus_constants" not in waveform_dict.keys() or type(waveform_dict["remote_focus_constants"]) is not DictProxy:
        update_config_dict(
            manager,
            waveform_dict,
            "remote_focus_constants",
            {}
        )
    
    waveform_dict = waveform_dict["remote_focus_constants"]
    for microscope_name in configuration["configuration"]["microscopes"].keys():
        config_dict = configuration["configuration"]["microscopes"][microscope_name]
        if microscope_name not in waveform_dict.keys() or type(waveform_dict[microscope_name]) is not DictProxy:
            update_config_dict(
                manager,
                waveform_dict,
                microscope_name,
                {}
            )

        # get lasers
        lasers = []
        for laser in config_dict["lasers"]:
            laser_wavelength = f"{laser['wavelength']}nm"
            lasers.append(laser_wavelength)

        for zoom in config_dict["zoom"]["position"].keys():
            if zoom not in waveform_dict[microscope_name].keys() or type(waveform_dict[microscope_name][zoom]) is not DictProxy:
                update_config_dict(
                    manager,
                    waveform_dict[microscope_name],
                    zoom,
                    {}
                )
            
            for laser in lasers:
                if laser not in waveform_dict[microscope_name][zoom].keys() or type(waveform_dict[microscope_name][zoom][laser]) is not DictProxy:
                    update_config_dict(
                        manager,
                        waveform_dict[microscope_name][zoom],
                        laser,
                        {
                            "amplitude": config_dict["remote_focus_device"]["amplitude"],
                            "offset": config_dict["remote_focus_device"]["offset"],
                            "percent_smoothing": "0",
                            "percent_delay": config_dict["remote_focus_device"]["delay_percent"]
                        }
                    )
                else:
                    for k in ["amplitude", "offset", "percent_smoothing", "percent_delay"]:
                        if k not in waveform_dict[microscope_name][zoom][laser].keys():
                            waveform_dict[microscope_name][zoom][laser][k] = config_dict["remote_focus_device"].get(k, "0")
                        else:
                            try:
                                float(waveform_dict[microscope_name][zoom][laser][k])
                            except ValueError:
                                waveform_dict[microscope_name][zoom][laser][k] = config_dict["remote_focus_device"].get(k, "0")
                    
            # delete non-exist lasers
            for k in waveform_dict[microscope_name][zoom].keys():
                if k not in lasers:
                    waveform_dict[microscope_name][zoom].pop(k)

        # delete non-exist zoom
        for k in waveform_dict[microscope_name].keys():
            if k not in config_dict["zoom"]["position"].keys():
                waveform_dict[microscope_name].pop(k)

    # delete non-exist microscope
    for k in waveform_dict.keys():
        if k not in configuration["configuration"]["microscopes"].keys():
            waveform_dict.pop(k)

    # galvo_constants
    waveform_dict = configuration["waveform_constants"]
    if "galvo_constants" not in waveform_dict.keys() or type(waveform_dict["galvo_constants"]) is not DictProxy:
        update_config_dict(
            manager,
            waveform_dict,
            "galvo_constants",
            {}
        )
    
    waveform_dict = waveform_dict["galvo_constants"]

    # get galvo num
    galvo_num = 0
    for microscope_name in configuration["configuration"]["microscopes"].keys():
        galvo_num = max(galvo_num, len(configuration["configuration"]["microscopes"][microscope_name]["galvo"]))

    for i in range(galvo_num):
        waveform_dict = configuration["waveform_constants"]["galvo_constants"]
        galvo_ref = f"Galvo {i}"
        if galvo_ref not in waveform_dict.keys() or type(waveform_dict[galvo_ref]) is not DictProxy:
            update_config_dict(
                manager,
                waveform_dict,
                galvo_ref,
                {}
            )
        waveform_dict = waveform_dict[galvo_ref]
        for microscope_name in configuration["configuration"]["microscopes"].keys():
            if len(configuration["configuration"]["microscopes"][microscope_name]["galvo"]) <= i:
                continue
            config_dict = configuration["configuration"]["microscopes"][microscope_name]
            if microscope_name not in waveform_dict.keys() or type(waveform_dict[microscope_name]) is not DictProxy:
                update_config_dict(
                    manager,
                    waveform_dict,
                    microscope_name,
                    {}
                )

            for zoom in config_dict["zoom"]["position"].keys():
                if zoom not in waveform_dict[microscope_name].keys() or type(waveform_dict[microscope_name][zoom]) is not DictProxy:
                    update_config_dict(
                        manager,
                        waveform_dict[microscope_name],
                        zoom,
                        {
                            "amplitude": "0.11",
                            "offset": config_dict["galvo"][i]["offset"],
                            "frequency": config_dict["galvo"][i]["frequency"]
                        }
                    )
                else:
                    for k in ["amplitude", "offset", "frequency"]:
                        if k not in waveform_dict[microscope_name][zoom].keys():
                            waveform_dict[microscope_name][zoom][k] = config_dict["galvo"][i].get(k, "0")
                        else:
                            try:
                                float(waveform_dict[microscope_name][zoom][k])
                            except ValueError:
                                waveform_dict[microscope_name][zoom][k] = config_dict["galvo"][i].get(k, "0")
            # delete non-exist zoom
            for k in waveform_dict[microscope_name].keys():
                if k not in config_dict["zoom"]["position"].keys():
                    waveform_dict[microscope_name].pop(k)
        # delete non-exist microscope
        for k in waveform_dict.keys():
            if k not in configuration["configuration"]["microscopes"].keys():
                waveform_dict.pop(k)

    # other_constants
    waveform_dict = configuration["waveform_constants"]
    if "other_constants" not in waveform_dict.keys() or type(waveform_dict["other_constants"]) is not DictProxy:
        update_config_dict(
            manager,
            waveform_dict,
            "other_constants",
            {"remote_focus_settle_duration": "0"}
        )
    if "remote_focus_settle_duration" not in waveform_dict["other_constants"].keys():
        waveform_dict["other_constants"]["remote_focus_settle_duration"] = "0"
    else:
        try:
            float(waveform_dict["other_constants"]["remote_focus_settle_duration"])
        except ValueError:
            waveform_dict["other_constants"]["remote_focus_settle_duration"] = "0"
