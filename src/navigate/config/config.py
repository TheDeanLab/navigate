# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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
import ast
import os
import sys
import time
import shutil
import platform
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from os.path import isfile
import multiprocessing
from multiprocessing.managers import ListProxy, DictProxy
import logging
from typing import Any, Optional, Tuple, Union

# Third Party Imports
import yaml

# Local Imports
from navigate.tools.common_functions import build_ref_name, load_param_from_module
from navigate.tools.file_functions import save_yaml_file

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

GUI_SETTING_DEFAULTS = {
    "remote_focus_waveform": {
        "amplitude_step_size": 0.0001,
        "offset_step_size": 0.0001,
    },
    "galvo_waveform": {
        "amplitude_step_size": 0.0001,
        "offset_step_size": 0.0001,
    },
}


def _channel_count(value):
    """Return a valid positive channel count, or ``None``.

    Channel counts in older configuration files may be written as strings.  A
    non-positive or otherwise invalid value must not suppress the configured
    fallback values.
    """
    try:
        count = int(value)
    except (TypeError, ValueError):
        return None
    return count if count > 0 else None


def _configuration_gui_channel_count(configuration):
    """Read the channel count from configuration.yaml's legacy GUI section."""
    configuration_yaml = configuration.get("configuration", {})
    legacy_gui = configuration_yaml.get("gui", {})
    if not hasattr(legacy_gui, "get"):
        return None

    channel_settings = legacy_gui.get("channel_settings", {})
    if hasattr(channel_settings, "get"):
        count = _channel_count(channel_settings.get("count"))
        if count is not None:
            return count

    # ``gui.channels.count`` is the layout used by historical
    # configuration.yaml files and remains supported during normalization.
    channels = legacy_gui.get("channels", {})
    return _channel_count(channels.get("count")) if hasattr(channels, "get") else None


def get_navigate_path():
    """Establish a program home directory in AppData/Local/.navigate for Windows
    or ~/.navigate for Mac and Linux.

    Returns
    -------
    str
        Path to Navigate home directory.
    """
    if platform.system() == "Windows":
        base_directory = os.getenv("LOCALAPPDATA")
    else:
        base_directory = os.getenv("HOME")
    navigate_path = os.path.join(base_directory, ".navigate")

    if not os.path.exists(navigate_path):
        os.mkdir(navigate_path)

    return navigate_path


def get_configuration_paths():
    """Get the paths of the various configuration files used by Navigate.

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
    gui_configuration_path : str
        Path to file containing GUI configuration
    multi_positions_path : str
        Path to file containing multi-positions
    """
    # Create the navigate home directory if it doesn't exist
    navigate_directory = get_navigate_path()
    if not os.path.exists(navigate_directory):
        os.mkdir(navigate_directory)

    # Create the configuration directory if it doesn't exist
    configuration_directory = Path(os.path.join(navigate_directory, "config"))
    if not os.path.exists(configuration_directory):
        os.mkdir(configuration_directory)

    configuration_files = [
        "configuration.yaml",
        "experiment.yml",
        "waveform_constants.yml",
        "rest_api_config.yml",
        "waveform_templates.yml",
        "gui_configuration.yml",
        "multi_positions.yml",
    ]

    base_directory = Path(__file__).resolve().parent
    paths = []
    for file in configuration_files:
        copy_file_path = Path.joinpath(base_directory, file)
        file_path = Path.joinpath(configuration_directory, file)
        paths.append(file_path)
        if not os.path.exists(file_path):
            shutil.copyfile(copy_file_path, file_path)

    return [path for path in paths]


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


def update_config_dict(
    manager: multiprocessing.Manager,
    parent_dict: dict,
    config_name: str,
    new_config: Union[dict, str],
) -> bool:
    """Read a new file and update info of the configuration dict.

    Parameters
    ----------
    manager : multiprocessing.Manager
        Shares objects (e.g., dict) between processes
    parent_dict : dict
        Dictionary we are adding to
    config_name : str
        Name of dictionary to replace
    new_config : dict or str
        Dictionary values or yaml file name

    Returns
    -------
    bool
        True or False
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
    if type(configuration["experiment"]) is not DictProxy:
        update_config_dict(manager, configuration, "experiment", {})

    # verify/build autofocus parameter setting
    # get autofocus supported devices(stages, remote_focus) from configuration.yaml file
    device_dict = {}
    # get devices: stages, NI remote_focus
    device_config = configuration["configuration"]["microscopes"]
    for microscope_name in device_config.keys():
        microscope_config = device_config[microscope_name]
        device_dict[microscope_name] = {}
        if (
            "remote_focus" in microscope_config.keys()
            and microscope_config["remote_focus"]["hardware"]["type"] == "NI"
        ):
            device_dict[microscope_name]["remote_focus"] = {}
            device_ref = microscope_config["remote_focus"]["hardware"]["channel"]
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
        "robust_fit": False,
        "spline_fit": False,
        "test_significance": False,
    }
    if (
        "AutoFocusParameters" not in configuration["experiment"]
        or type(configuration["experiment"]["AutoFocusParameters"]) is not DictProxy
    ):
        update_config_dict(
            manager, configuration["experiment"], "AutoFocusParameters", {}
        )
    autofocus_setting_dict = configuration["experiment"]["AutoFocusParameters"]
    # verify if all the devices have been added to the autofocus parameter dict
    for microscope_name in device_dict:
        if microscope_name not in autofocus_setting_dict.keys():
            update_config_dict(manager, autofocus_setting_dict, microscope_name, {})
        for device in device_dict[microscope_name]:
            if device not in autofocus_setting_dict[microscope_name].keys():
                update_config_dict(
                    manager,
                    autofocus_setting_dict[microscope_name],
                    device,
                    {},
                )
            for device_ref in device_dict[microscope_name][device]:
                if (
                    device_ref
                    not in autofocus_setting_dict[microscope_name][device].keys()
                ):
                    update_config_dict(
                        manager,
                        autofocus_setting_dict[microscope_name][device],
                        device_ref,
                        autofocus_sample_setting,
                    )
                else:
                    # add missing parameters
                    for k in autofocus_sample_setting.keys():
                        if (
                            k
                            not in autofocus_setting_dict[microscope_name][device][
                                device_ref
                            ].keys()
                        ):
                            autofocus_setting_dict[microscope_name][device][device_ref][
                                k
                            ] = autofocus_sample_setting[k]

    # remove non-consistent autofocus parameter
    for microscope_name in autofocus_setting_dict.keys():
        if microscope_name not in device_dict:
            autofocus_setting_dict.pop(microscope_name)
        else:
            for device in autofocus_setting_dict[microscope_name].keys():
                if device not in device_dict[microscope_name]:
                    autofocus_setting_dict[microscope_name].pop(device)
                else:
                    for device_ref in autofocus_setting_dict[microscope_name][
                        device
                    ].keys():
                        if (
                            device_ref
                            not in autofocus_setting_dict[microscope_name][device]
                        ):
                            autofocus_setting_dict[microscope_name][device].pop(
                                device_ref
                            )

    # saving info
    saving_dict_sample = {
        "root_directory": get_navigate_path(),
        "save_directory": get_navigate_path(),
        "user": "Kevin",
        "tissue": "Lung",
        "celltype": "MV3",
        "label": "GFP",
        "file_type": "TIFF",
        "prefix": "Cell_",
        "date": time.strftime("%Y-%m-%d"),
        "solvent": "BABB",
    }
    if (
        "Saving" not in configuration["experiment"]
        or type(configuration["experiment"]["Saving"]) is not DictProxy
    ):
        update_config_dict(
            manager, configuration["experiment"], "Saving", saving_dict_sample
        )
    saving_setting_dict = configuration["experiment"]["Saving"]
    for k in saving_dict_sample:
        if k not in saving_setting_dict:
            saving_setting_dict[k] = saving_dict_sample[k]

    # if root directory/saving directory doesn't exist
    if not os.path.exists(saving_setting_dict["root_directory"]):
        saving_setting_dict["root_directory"] = saving_dict_sample["root_directory"]
    if not os.path.exists(saving_setting_dict["save_directory"]):
        saving_setting_dict["save_directory"] = saving_dict_sample["save_directory"]

    # camera parameters
    camera_parameters_dict_sample = {
        "x_pixels": 2048,
        "y_pixels": 2048,
        "img_x_pixels": 2048,
        "img_y_pixels": 2048,
        "sensor_mode": "Normal",
        "readout_direction": "Top-to-Bottom",
        "number_of_pixels": 10,
        "binning": "1x1",
        "databuffer_size": 100,
        "is_centered": True,
        "center_x": 1024,
        "center_y": 1024,
        "readout_time": 0,
    }
    if (
        "CameraParameters" not in configuration["experiment"]
        or type(configuration["experiment"]["CameraParameters"]) is not DictProxy
    ):
        update_config_dict(
            manager,
            configuration["experiment"],
            "CameraParameters",
            camera_parameters_dict_sample,
        )
    microscope_names = [""] + list(configuration["configuration"]["microscopes"].keys())
    for microscope_name in microscope_names:
        camera_setting_dict = configuration["experiment"]["CameraParameters"]
        if microscope_name:
            if (
                microscope_name not in camera_setting_dict
                or type(camera_setting_dict[microscope_name]) is not DictProxy
            ):
                update_config_dict(
                    manager,
                    camera_setting_dict,
                    microscope_name,
                    camera_parameters_dict_sample,
                )
            camera_setting_dict = camera_setting_dict[microscope_name]

        for k in camera_parameters_dict_sample:
            if k not in camera_setting_dict.keys():
                camera_setting_dict[k] = camera_parameters_dict_sample[k]
        # binning
        if camera_setting_dict["binning"] not in ["1x1", "2x2", "4x4"]:
            camera_setting_dict["binning"] = "1x1"
        # x_pixels and y_pixels
        try:
            camera_setting_dict["x_pixels"] = int(camera_setting_dict["x_pixels"])
        except ValueError:
            camera_setting_dict["x_pixels"] = camera_parameters_dict_sample["x_pixels"]

        try:
            camera_setting_dict["y_pixels"] = int(camera_setting_dict["y_pixels"])
        except ValueError:
            camera_setting_dict["y_pixels"] = camera_parameters_dict_sample["y_pixels"]

        # image width and height
        if camera_setting_dict["x_pixels"] <= 0:
            camera_setting_dict["x_pixels"] = camera_parameters_dict_sample["x_pixels"]
        if camera_setting_dict["y_pixels"] <= 0:
            camera_setting_dict["y_pixels"] = camera_parameters_dict_sample["y_pixels"]
        x_binning = int(camera_setting_dict["binning"][0])
        y_binning = int(camera_setting_dict["binning"][2])
        img_x_pixels = camera_setting_dict["x_pixels"] // x_binning
        img_y_pixels = camera_setting_dict["y_pixels"] // y_binning
        camera_setting_dict["img_x_pixels"] = img_x_pixels
        camera_setting_dict["img_y_pixels"] = img_y_pixels
        if camera_setting_dict["is_centered"]:
            camera_setting_dict["center_x"] = camera_setting_dict["x_pixels"] // 2
            camera_setting_dict["center_y"] = camera_setting_dict["y_pixels"] // 2

        # sensor mode
        if camera_setting_dict["sensor_mode"] not in ["Normal", "Light-Sheet"]:
            camera_setting_dict["sensor_mode"] = "Normal"
        if camera_setting_dict["readout_direction"] not in [
            "Top-to-Bottom",
            "Bottom-to-Top",
            "Bidirectional",
            "Rev. Bidirectional",
        ]:
            camera_setting_dict["readout_direction"] = "Top-to-Bottom"

        # databuffer_size, number_of_pixels
        for k in ["databuffer_size", "number_of_pixels"]:
            try:
                camera_setting_dict[k] = int(camera_setting_dict[k])
            except ValueError:
                camera_setting_dict[k] = camera_parameters_dict_sample[k]
            if camera_setting_dict[k] < 1:
                camera_setting_dict[k] = camera_parameters_dict_sample[k]

    # stage parameters
    stage_dict_sample = {}
    device_config = configuration["configuration"]["microscopes"]
    for microscope_name in device_config.keys():
        stage_dict_sample[microscope_name] = {}
        for k in ["z_step", "f_step", "theta_step"]:
            stage_dict_sample[microscope_name][k] = int(
                device_config[microscope_name]["stage"].get(k, 30)
            )
        stage_dict_sample[microscope_name]["xy_step"] = min(
            device_config[microscope_name]["stage"].get("x_step", 500),
            device_config[microscope_name]["stage"].get("y_step", 500),
        )

    if (
        "StageParameters" not in configuration["experiment"]
        or type(configuration["experiment"]["StageParameters"]) is not DictProxy
    ):
        update_config_dict(
            manager, configuration["experiment"], "StageParameters", stage_dict_sample
        )
    stage_setting_dict = configuration["experiment"]["StageParameters"]
    if "limits" not in stage_setting_dict.keys():
        stage_setting_dict["limits"] = True
    elif type(stage_setting_dict["limits"]) is not bool:
        stage_setting_dict["limits"] = True

    for microscope_name in stage_dict_sample:
        if (
            microscope_name not in stage_setting_dict.keys()
            or type(stage_setting_dict[microscope_name]) is not DictProxy
        ):
            update_config_dict(
                manager,
                stage_setting_dict,
                microscope_name,
                stage_dict_sample[microscope_name],
            )
        else:
            for k in stage_dict_sample[microscope_name]:
                if k not in stage_setting_dict[microscope_name].keys():
                    stage_setting_dict[microscope_name][k] = stage_dict_sample[
                        microscope_name
                    ][k]
                else:
                    try:
                        stage_setting_dict[microscope_name][k] = int(
                            stage_setting_dict[microscope_name][k]
                        )
                    except ValueError:
                        stage_setting_dict[microscope_name][k] = stage_dict_sample[
                            microscope_name
                        ][k]

    # microscope state parameters
    microscope_name = configuration["configuration"]["microscopes"].keys()[0]
    zoom = configuration["configuration"]["microscopes"][microscope_name]["zoom"][
        "position"
    ].keys()[0]
    microscope_state_dict_sample = {
        "microscope_name": microscope_name,
        "image_mode": "live",
        "zoom": zoom,
        "stack_cycling_mode": "per_stack",
        "start_position": 0.0,
        "end_position": 100.0,
        "step_size": 20.0,
        "number_z_steps": 5,
        "timepoints": 1,
        "stack_pause": 0.0,
        "is_save": False,
        "stack_acq_time": 1.0,
        "timepoint_interval": 0,
        "experiment_duration": 1.03,
        "is_multiposition": False,
        "stack_z_origin": 0,
        "stack_focus_origin": 0,
        "start_focus": 0.0,
        "end_focus": 0.0,
        "abs_z_start": 0.0,
        "abs_z_end": 100.0,
        "waveform_template": "Default",
    }
    if (
        "MicroscopeState" not in configuration["experiment"]
        or type(configuration["experiment"]["MicroscopeState"]) is not DictProxy
    ):
        update_config_dict(
            manager,
            configuration["experiment"],
            "MicroscopeState",
            microscope_state_dict_sample,
        )
    microscope_setting_dict = configuration["experiment"]["MicroscopeState"]
    for k in microscope_state_dict_sample:
        if k not in microscope_setting_dict.keys():
            microscope_setting_dict[k] = microscope_state_dict_sample[k]
        elif not isinstance(
            microscope_setting_dict[k], type(microscope_state_dict_sample[k])
        ):
            if isinstance(microscope_state_dict_sample[k], float):
                try:
                    microscope_setting_dict[k] = float(microscope_setting_dict[k])
                except ValueError:
                    microscope_setting_dict[k] = microscope_state_dict_sample[k]
            elif isinstance(microscope_state_dict_sample[k], int):
                try:
                    microscope_setting_dict[k] = int(microscope_setting_dict[k])
                except ValueError:
                    microscope_setting_dict[k] = microscope_state_dict_sample[k]
            else:
                microscope_setting_dict[k] = microscope_state_dict_sample[k]

    # verify microscope name
    if (
        microscope_setting_dict["microscope_name"]
        not in configuration["configuration"]["microscopes"].keys()
    ):
        microscope_setting_dict["microscope_name"] = microscope_name
    microscope_name = microscope_setting_dict["microscope_name"]
    # zoom
    if (
        microscope_setting_dict["zoom"]
        not in configuration["configuration"]["microscopes"][microscope_name]["zoom"][
            "position"
        ].keys()
    ):
        microscope_setting_dict["zoom"] = configuration["configuration"]["microscopes"][
            microscope_name
        ]["zoom"]["position"].keys()[0]
    # channels
    if (
        "channels" not in microscope_setting_dict
        or type(microscope_setting_dict["channels"]) is not DictProxy
    ):
        update_config_dict(manager, microscope_setting_dict, "channels", {})
    laser_list = [
        f"{laser['wavelength']}nm"
        for laser in configuration["configuration"]["microscopes"][microscope_name][
            "laser"
        ]
    ]
    number_of_filter_wheels = len(
        configuration["configuration"]["microscopes"][microscope_name].get(
            "filter_wheel", []
        )
    )
    filterwheel_list = [
        list(filter_wheel_config["available_filters"].keys())
        for filter_wheel_config in configuration["configuration"]["microscopes"][
            microscope_name
        ].get("filter_wheel", [])
    ]
    prefix = "channel_"
    channel_nums = configuration["gui"].get("channel_settings", {}).get("count", 5)
    channel_setting_dict = microscope_setting_dict["channels"]
    selected_channel_num = 0
    for channel in channel_setting_dict.keys():
        if not channel.startswith(prefix):
            del channel_setting_dict[channel]
            continue
        channel_id = int(channel[len(prefix) :]) - 1
        if channel_id < 0 or channel_id >= channel_nums:
            del channel_setting_dict[channel]
            continue
        channel_value = channel_setting_dict[channel]
        # make sure channel values are right
        # laser
        if channel_value["laser"] not in laser_list:
            channel_value["laser"] = laser_list[0]
        channel_value["laser_index"] = laser_list.index(channel_value["laser"])
        # filter wheel
        for i in range(number_of_filter_wheels):
            ref_name = configuration["configuration"]["microscopes"][microscope_name][
                "filter_wheel"
            ][i].get("name", f"FilterWheel-{i}")
            if (
                ref_name not in channel_value
                or channel_value[ref_name] not in filterwheel_list[i]
            ):
                channel_value[ref_name] = filterwheel_list[i][0]
        if "filter" in channel_value:
            channel_value.pop("filter")
        # is_selected
        if (
            "is_selected" not in channel_value.keys()
            or type(channel_value["is_selected"]) != bool
        ):
            channel_value["is_selected"] = False
        if channel_value["is_selected"]:
            selected_channel_num += 1
        # camera_exposure_time and defoucus should be float
        temp = {
            "laser_power": 20.0,
            "camera_exposure_time": 200.0,
            "interval_time": 0.0,
            "defocus": 0.0,
        }
        for k in temp:
            try:
                channel_value[k] = float(channel_value[k])
            except ValueError:
                channel_value[k] = temp[k]
            if k != "defocus" and channel_value[k] < 0:
                channel_value[k] = temp[k]


def verify_waveform_constants(manager, configuration):
    """Verifies and updates the waveform constants in the configuration dictionary.

    This function checks and ensures that the waveform constants in the given
    configuration dictionary conform to the expected structure. It verifies and
    updates the constants related to remote focus devices, lasers, and galvos
    for multiple microscopes.

    Parameters
    ----------
    manager : multiprocessing.Manager
        Shares objects (e.g., dict) between processes
    configuration : dict
        The configuration dictionary containing waveform constants.

    Note
    ----
        If constants are missing or not in the expected structure, default values
        or empty dictionaries are added as necessary.
    Note
    ----
        Laser and galvo constants are validated and converted to float if possible.
    Note
    ----
        Non-existent microscopes, zoom levels, lasers, and galvos are removed
        from the configuration.

    """
    if type(configuration["waveform_constants"]) is not DictProxy:
        update_config_dict(manager, configuration, "waveform_constants", {})
    waveform_dict = configuration["waveform_constants"]

    # remote_focus_constants
    if (
        "remote_focus_constants" not in waveform_dict.keys()
        or type(waveform_dict["remote_focus_constants"]) is not DictProxy
    ):
        update_config_dict(manager, waveform_dict, "remote_focus_constants", {})

    waveform_dict = waveform_dict["remote_focus_constants"]
    for microscope_name in configuration["configuration"]["microscopes"].keys():
        config_dict = configuration["configuration"]["microscopes"][microscope_name]
        if (
            microscope_name not in waveform_dict.keys()
            or type(waveform_dict[microscope_name]) is not DictProxy
        ):
            update_config_dict(manager, waveform_dict, microscope_name, {})

        # get laser
        lasers = []
        for laser in config_dict["laser"]:
            laser_wavelength = f"{laser['wavelength']}nm"
            lasers.append(laser_wavelength)

        for zoom in config_dict["zoom"]["position"].keys():
            if (
                zoom not in waveform_dict[microscope_name].keys()
                or type(waveform_dict[microscope_name][zoom]) is not DictProxy
            ):
                update_config_dict(manager, waveform_dict[microscope_name], zoom, {})

            for laser in lasers:
                if (
                    laser not in waveform_dict[microscope_name][zoom].keys()
                    or type(waveform_dict[microscope_name][zoom][laser])
                    is not DictProxy
                ):
                    update_config_dict(
                        manager,
                        waveform_dict[microscope_name][zoom],
                        laser,
                        {
                            "amplitude": 0,
                            "offset": 0,
                            # "percent_smoothing": "0",
                            # "delay": config_dict["remote_focus"][
                            #     "delay"
                            # ],
                        },
                    )
                else:
                    for k in [
                        "amplitude",
                        "offset",
                        # "percent_smoothing",
                        # "delay",
                    ]:
                        if k not in waveform_dict[microscope_name][zoom][laser].keys():
                            waveform_dict[microscope_name][zoom][laser][k] = (
                                config_dict["remote_focus"].get(k, "0")
                            )
                        else:
                            try:
                                float(waveform_dict[microscope_name][zoom][laser][k])
                            except ValueError:
                                waveform_dict[microscope_name][zoom][laser][k] = (
                                    config_dict["remote_focus"].get(k, "0")
                                )

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
    if (
        "galvo_constants" not in waveform_dict.keys()
        or type(waveform_dict["galvo_constants"]) is not DictProxy
    ):
        update_config_dict(manager, waveform_dict, "galvo_constants", {})

    waveform_dict = waveform_dict["galvo_constants"]

    # get galvo num
    galvo_num = 0
    for microscope_name in configuration["configuration"]["microscopes"].keys():
        galvo_num = max(
            galvo_num,
            len(
                configuration["configuration"]["microscopes"][microscope_name]["galvo"]
            ),
        )

    for i in range(galvo_num):
        waveform_dict = configuration["waveform_constants"]["galvo_constants"]
        galvo_ref = f"Galvo {i}"
        if (
            galvo_ref not in waveform_dict.keys()
            or type(waveform_dict[galvo_ref]) is not DictProxy
        ):
            update_config_dict(manager, waveform_dict, galvo_ref, {})
        waveform_dict = waveform_dict[galvo_ref]
        for microscope_name in configuration["configuration"]["microscopes"].keys():
            if (
                len(
                    configuration["configuration"]["microscopes"][microscope_name][
                        "galvo"
                    ]
                )
                <= i
            ):
                continue
            config_dict = configuration["configuration"]["microscopes"][microscope_name]
            if (
                microscope_name not in waveform_dict.keys()
                or type(waveform_dict[microscope_name]) is not DictProxy
            ):
                update_config_dict(manager, waveform_dict, microscope_name, {})

            galvo_config = {
                "amplitude": "0",
                "offset": 0,
                "rising_ramp": 50,
                "frequency": 10,
            }
            for zoom in config_dict["zoom"]["position"].keys():
                if (
                    zoom not in waveform_dict[microscope_name].keys()
                    or type(waveform_dict[microscope_name][zoom]) is not DictProxy
                ):
                    update_config_dict(
                        manager,
                        waveform_dict[microscope_name],
                        zoom,
                        galvo_config,
                    )
                else:
                    for k in galvo_config.keys():
                        if k not in waveform_dict[microscope_name][zoom].keys():
                            waveform_dict[microscope_name][zoom][k] = config_dict[
                                "galvo"
                            ][i].get(k, galvo_config[k])
                        else:
                            try:
                                float(waveform_dict[microscope_name][zoom][k])
                            except ValueError:
                                waveform_dict[microscope_name][zoom][k] = config_dict[
                                    "galvo"
                                ][i].get(k, "0")
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
    microscope_name = configuration["configuration"]["microscopes"].keys()[0]
    camera_config = configuration["configuration"]["microscopes"][microscope_name][
        "camera"
    ]
    other_constants_dict = {
        "remote_focus_settle_duration": "0",
        "percent_smoothing": "0",
        "remote_focus_delay": "0",
        "remote_focus_ramp_falling": "5",
        "camera_settle_duration": "0",
        "camera_delay": camera_config.get(
            "delay", camera_config.get("delay_percent", "1.0")
        ),
    }
    if (
        "other_constants" not in waveform_dict.keys()
        or type(waveform_dict["other_constants"]) is not DictProxy
    ):
        update_config_dict(
            manager,
            waveform_dict,
            "other_constants",
            other_constants_dict,
        )
    for k in other_constants_dict.keys():
        try:
            float(waveform_dict["other_constants"][k])
        except (ValueError, KeyError):
            waveform_dict["other_constants"][k] = other_constants_dict[k]


def verify_configuration(manager, configuration):
    """Verify configuration files.

    Supports old version of configurations.
    """
    support_deceased_configuration(configuration)
    device_config = configuration["configuration"]["microscopes"]
    # get microscope inheritance sequence
    microscope_name_seq = []
    inherited_microscope_dict = {}
    microscope_names_list = list(device_config.keys())
    for microscope_name in microscope_names_list:
        try:
            parenthesis_l = microscope_name.index("(")
        except ValueError:
            if microscope_name.strip() not in microscope_name_seq:
                microscope_name_seq.append(microscope_name.strip())
            continue

        if ")" not in microscope_name[parenthesis_l + 1 :]:
            microscope_name_seq.append(microscope_name.strip())
            continue

        parenthesis_r = microscope_name[parenthesis_l + 1 :].index(")")
        parent_microscope_name = microscope_name[
            parenthesis_l + 1 : parenthesis_l + parenthesis_r + 1
        ].strip()

        if parent_microscope_name not in microscope_name_seq:
            microscope_name_seq.append(parent_microscope_name)

        idx = microscope_name_seq.index(parent_microscope_name)
        child_microscope_name = microscope_name[:parenthesis_l].strip()
        microscope_name_seq.insert(idx + 1, child_microscope_name)
        inherited_microscope_dict[child_microscope_name] = parent_microscope_name
        device_config[child_microscope_name] = device_config.pop(microscope_name)

    # update microscope devices from parent microscope
    for microscope_name in microscope_name_seq:
        if microscope_name not in inherited_microscope_dict:
            continue
        parent_microscope_name = inherited_microscope_dict[microscope_name]
        if parent_microscope_name not in device_config.keys():
            logger.error(
                f"Microscope {parent_microscope_name} is not defined in "
                f"configuration.yaml"
            )
            raise Exception(
                f"Microscope {parent_microscope_name} is not "
                f"defined in configuration.yaml"
            )

        for device_name in device_config[parent_microscope_name].keys():
            if device_name not in device_config[microscope_name].keys():
                device_config[microscope_name][device_name] = device_config[
                    parent_microscope_name
                ][device_name]

    camera_channel_counts = []
    # generate hardware header section
    ref_list = {
        "filter_wheel": [],
    }
    required_devices = [
        "camera",
        "shutter",
        "remote_focus",
        "galvo",
        "stage",
        "laser",
    ]
    filter_wheel_seq = []
    for microscope_name in device_config.keys():
        for device_name in required_devices:
            if device_name not in device_config[microscope_name]:
                print(
                    f"Please make sure you have {device_name} "
                    f"in the configuration for microscope {microscope_name}, or "
                    f"{microscope_name} is inherited from another valid microscope!"
                )
                logger.error(
                    f"{device_name} is not defined in configuration.yaml for "
                    f"microscope {microscope_name}"
                )
                raise Exception(
                    f"No {device_name} defined for microscope {microscope_name}"
                )
        camera_config = device_config[microscope_name]["camera"]
        camera_channel_count = _channel_count(camera_config.get("count"))
        if camera_channel_count is not None:
            camera_channel_counts.append(camera_channel_count)

        # laser
        for i, laser_config in enumerate(device_config[microscope_name]["laser"]):
            onoff_type = laser_config["onoff"]["hardware"].get("type", "Synthetic")
            power_type = laser_config["power"]["hardware"].get("type", "Synthetic")
            if onoff_type != "Synthetic":
                laser_hardware_config = dict(laser_config["onoff"]["hardware"])
            elif power_type != "Synthetic":
                laser_hardware_config = dict(laser_config["power"]["hardware"])
            else:
                laser_hardware_config = {"type": "Synthetic"}
            laser_hardware_config["wavelength"] = laser_config["wavelength"]

            update_config_dict(manager, laser_config, "hardware", laser_hardware_config)

        # zoom
        zoom_config = device_config[microscope_name]["zoom"]
        if "hardware" not in zoom_config:
            update_config_dict(
                manager, zoom_config, "hardware", {"type": "Synthetic", "servo_id": 0}
            )
        elif "type" not in zoom_config["hardware"]:
            zoom_config["hardware"]["type"] = "Synthetic"

        filter_wheel_config = device_config[microscope_name].get("filter_wheel", None)
        if filter_wheel_config is None:
            continue

        if type(filter_wheel_config) == DictProxy:
            # support older version of configuration.yaml
            # filter_wheel_delay and available filters
            update_config_dict(
                manager,
                device_config[microscope_name],
                "filter_wheel",
                [filter_wheel_config],
            )

        temp_config = device_config[microscope_name]["filter_wheel"]
        filter_wheel_names = set()
        for _, filter_wheel_config in enumerate(temp_config):
            name = filter_wheel_config.get("name")
            hardware_name = filter_wheel_config.get("hardware", {}).get("name")
            if not isinstance(name, str) or not name.strip():
                filter_wheel_config["name"] = None
            if not isinstance(hardware_name, str) or not hardware_name.strip():
                hardware_name = None
            filter_wheel_idx = build_ref_name(
                "-",
                filter_wheel_config["hardware"]["type"],
                filter_wheel_config["hardware"]["wheel_number"],
            )
            if filter_wheel_idx not in ref_list["filter_wheel"]:
                ref_list["filter_wheel"].append(filter_wheel_idx)
                filter_wheel_seq.append(filter_wheel_config)
                if filter_wheel_config.get("name", None) is None and hardware_name:
                    filter_wheel_config["name"] = hardware_name
            idx = ref_list["filter_wheel"].index(filter_wheel_idx)
            if filter_wheel_seq[idx].get("name", None):
                filter_wheel_config["name"] = filter_wheel_seq[idx]["name"]
            elif filter_wheel_config.get("name", None):
                filter_wheel_seq[idx]["name"] = filter_wheel_config["name"]
            elif hardware_name:
                filter_wheel_seq[idx]["name"] = hardware_name
            if filter_wheel_seq[idx].get("name", None):
                if filter_wheel_seq[idx]["name"] not in filter_wheel_names:
                    filter_wheel_names.add(filter_wheel_seq[idx]["name"])
                else:
                    filter_wheel_seq[idx]["name"] = None

    # make sure all filter wheel entries have hardware name
    for i, filter_wheel_config in enumerate(filter_wheel_seq):
        if not filter_wheel_config.get("name"):
            for j in range(len(filter_wheel_seq)):
                temp_name = f"FilterWheel-{j}"
                if temp_name not in filter_wheel_names:
                    filter_wheel_seq[i]["name"] = temp_name
                    filter_wheel_names.add(temp_name)
                    break

    # make sure all microscopes have the same filter wheel sequence
    if len(filter_wheel_seq) > 0:
        for microscope_name in device_config.keys():
            temp_config = device_config[microscope_name].get("filter_wheel", None)
            if temp_config is None:
                continue
            for i, filter_wheel_config in enumerate(temp_config):
                filter_wheel_idx = build_ref_name(
                    "-",
                    filter_wheel_config["hardware"]["type"],
                    filter_wheel_config["hardware"]["wheel_number"],
                )
                idx = ref_list["filter_wheel"].index(filter_wheel_idx)
                temp_config[i]["name"] = filter_wheel_seq[idx]["name"]

    gui_settings = configuration["gui"]
    channel_settings = gui_settings.get("channel_settings")
    if not hasattr(channel_settings, "get"):
        update_config_dict(manager, gui_settings, "channel_settings", {})
        channel_settings = gui_settings["channel_settings"]

    channel_count = _channel_count(channel_settings.get("count"))
    if channel_count is None:
        channel_count = _configuration_gui_channel_count(configuration)
    if channel_count is None and camera_channel_counts:
        channel_count = max(camera_channel_counts)
    if channel_count is None:
        channel_count = 5
    channel_settings["count"] = channel_count
    for group_name, defaults in GUI_SETTING_DEFAULTS.items():
        if group_name not in gui_settings:
            update_config_dict(manager, gui_settings, group_name, defaults)
            continue
        for setting_name, value in defaults.items():
            if setting_name not in gui_settings[group_name]:
                gui_settings[group_name][setting_name] = value


def verify_positions_config(positions):
    if positions is None or type(positions) not in (list, ListProxy):
        return []
    # MultiPositions
    # check if there is a header
    start_index = 0
    if len(positions) > 0:
        cmp_header = [axis in positions[0] for axis in ["X", "Y"]]
        if all(cmp_header):
            start_index = 1
        elif any(cmp_header):
            positions = positions[1:]
            start_index = 0
        else:
            start_index = 0

    if start_index == len(positions):
        return []

    position_num = len(positions)
    for i in range(position_num - 1, start_index - 1, -1):
        position = positions[i]
        try:
            for j in range(len(position)):
                float(position[j])
        except (ValueError, KeyError, IndexError):
            del positions[i]

    return positions


def support_deceased_configuration(configuration):
    """Support old version of configurations.

    Parameters
    ----------
    configuration : dict
        The configuration dictionary containing old version configurations.

    Note
    ----
    This function updates the configuration dictionary to support old version
    configurations by renaming keys and updating values as necessary.
    """

    device_config = configuration["configuration"]["microscopes"]
    is_updated = False
    for microscope_name in device_config.keys():
        microscope_config = device_config[microscope_name]
        if "remote_focus_device" in microscope_config.keys():
            microscope_config["remote_focus"] = microscope_config.pop(
                "remote_focus_device"
            )
            is_updated = True
        if "lasers" in microscope_config.keys():
            microscope_config["laser"] = microscope_config.pop("lasers")
            is_updated = True
        if "stage" in microscope_config.keys():
            deceased_device_type_names = load_param_from_module(
                "navigate.config.configuration_database", "deceased_device_type_names"
            )
            if "hardware" not in microscope_config["stage"]:
                continue
            stage_config = microscope_config["stage"]["hardware"]
            if type(stage_config) is not ListProxy:
                stage_config = [stage_config]
            for stage in stage_config:
                if (
                    hasattr(stage, "keys")
                    and "type" in stage
                    and stage["type"] in deceased_device_type_names
                ):
                    stage["type"] = deceased_device_type_names[stage["type"]]
                    is_updated = True


class PreloadPolicy(str, Enum):
    """Specify how the configuration preloader handles invalid hardware."""

    STRICT = "strict"
    WARN = "warn"
    SYNTHETIC_FALLBACK = "synthetic_fallback"


@dataclass(frozen=True)
class ValidationIssue:
    """One issue found while preparing configuration for application startup."""

    severity: str
    path: str
    message: str
    action_taken: str = "none"


@dataclass
class PreloadResult:
    """Shared configuration and diagnostics returned by :func:`preload_configuration`."""

    configuration: dict
    issues: list[ValidationIssue]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Return non-blocking diagnostics suitable for a startup dialog."""
        return [issue for issue in self.issues if issue.severity == "warning"]


class ConfigurationValidationError(RuntimeError):
    """Raised when strict preloading finds invalid configuration."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues
        super().__init__(
            "Configuration validation failed: "
            + "; ".join(issue.message for issue in issues)
        )


@dataclass(frozen=True)
class SchemaSettingSpec:
    """Local, import-safe representation of a device ``SettingSpec`` literal."""

    value_type: type
    default: Any = None
    label: Optional[str] = None
    help_text: Optional[str] = None
    choices: Optional[Tuple[Any, ...]] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None
    required: bool = False


class DeviceSchemaResolver:
    """Read inherited device schemas without importing device SDK modules.

    Device modules can import optional vendor libraries.  The schemas are
    declarative literals, therefore reading their AST keeps startup validation
    independent of those libraries and matches the configurator's behavior.
    """

    _category_suffixes = {
        "camera": "Camera",
        "daq": "DAQ",
        "filter_wheel": "FilterWheel",
        "galvo": "Galvo",
        "laser": "Laser",
        "remote_focus": "RemoteFocus",
        "shutter": "Shutter",
        "stage": "Stage",
        "zoom": "Zoom",
    }

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], dict[str, object]] = {}
        self._devices_directory = (
            Path(__file__).resolve().parents[1] / "model" / "devices"
        )

    def get_schema(self, category: str, device_type: str) -> dict[str, object]:
        """Return all schema entries declared by a device and its parents."""
        cache_key = (category, device_type)
        if cache_key in self._cache:
            return self._cache[cache_key]
        class_path, class_name = self._find_device_class(category, device_type)
        if class_path is None or class_name is None:
            self._cache[cache_key] = {}
            return {}
        schema = self._schema_from_file(class_path, class_name, set())
        self._cache[cache_key] = schema
        return schema

    def _find_device_class(
        self, category: str, device_type: str
    ) -> Tuple[Optional[Path], Optional[str]]:
        directory = self._devices_directory / category
        if not directory.exists():
            return None, None
        suffix = self._category_suffixes[category]
        short_device_type = (
            device_type[: -len(suffix)]
            if device_type.lower().endswith(suffix.lower())
            else device_type
        )
        candidates = {
            device_type.lower(),
            f"{device_type}{suffix}".lower(),
            short_device_type.lower(),
            f"{short_device_type}{suffix}".lower(),
        }
        for path in directory.glob("*.py"):
            if path.name in {"__init__.py", "base.py"}:
                continue
            module = ast.parse(path.read_text(encoding="utf-8"))
            for node in module.body:
                if isinstance(node, ast.ClassDef) and node.name.lower() in candidates:
                    return path, node.name
        return None, None

    def _schema_from_file(
        self, path: Path, class_name: str, visited: set[tuple[Path, str]]
    ) -> dict[str, object]:
        key = (path, class_name)
        if key in visited:
            return {}
        visited.add(key)
        module = ast.parse(path.read_text(encoding="utf-8"))
        nodes = {
            node.name: node for node in module.body if isinstance(node, ast.ClassDef)
        }
        node = nodes.get(class_name)
        if node is None:
            return {}
        schemas = []
        for base in node.bases:
            base_name = base.id if isinstance(base, ast.Name) else ""
            if base_name in nodes:
                schemas.append(self._schema_from_file(path, base_name, visited))
            elif base_name in {"SerialDevice", "SequenceDevice"}:
                schemas.append(
                    self._schema_from_file(
                        self._devices_directory / "device_types.py",
                        base_name,
                        visited,
                    )
                )
            elif base_name.endswith("Base"):
                schemas.append(
                    self._schema_from_file(path.parent / "base.py", base_name, visited)
                )
        schemas.append(self._class_schema(node))
        merged = {}
        for schema in schemas:
            merged.update(schema)
        return merged

    @staticmethod
    def _class_schema(node: ast.ClassDef) -> dict[str, object]:
        for statement in node.body:
            if not (
                isinstance(statement, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "configuration_schema"
                    for target in statement.targets
                )
                and isinstance(statement.value, ast.Dict)
            ):
                continue
            schema = {}
            for key, value in zip(statement.value.keys, statement.value.values):
                if not (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(value, ast.Call)
                ):
                    continue
                spec = DeviceSchemaResolver._setting_spec(value)
                if spec is not None:
                    schema[key.value] = spec
            return schema
        return {}

    @staticmethod
    def _setting_spec(call: ast.Call) -> Optional[SchemaSettingSpec]:
        if not (
            isinstance(call.func, ast.Name)
            and call.func.id == "SettingSpec"
            and call.args
            and isinstance(call.args[0], ast.Name)
        ):
            return None
        value_type = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
        }.get(call.args[0].id)
        if value_type is None:
            return None
        kwargs = {}
        for keyword in call.keywords:
            if keyword.arg is None:
                continue
            try:
                kwargs[keyword.arg] = ast.literal_eval(keyword.value)
            except ValueError:
                continue
        return SchemaSettingSpec(value_type, **kwargs)


REQUIRED_DEVICE_DEFAULTS = {
    "daq": {
        "hardware": {"type": "Synthetic"},
        "sample_rate": 100000,
    },
    "camera": {
        "hardware": {
            "type": "Synthetic",
            "serial_number": "SYNTHETIC-CAMERA-0",
        },
    },
    "remote_focus": {
        "hardware": {
            "type": "Synthetic",
            "channel": "Synthetic/ao0",
            "min": -5.0,
            "max": 5.0,
        },
    },
    "galvo": [
        {
            "hardware": {
                "type": "Synthetic",
                "channel": "Synthetic/ao0",
                "min": -5.0,
                "max": 5.0,
            },
            "phase": 1.57079,
        }
    ],
    "stage": {
        "hardware": [
            {
                "type": "Synthetic",
                "serial_number": "SYNTHETIC-STAGE-0",
                "axes": ["x", "y", "z", "theta", "f"],
            }
        ],
        "x_min": -100000,
        "x_max": 100000,
        "y_min": -100000,
        "y_max": 100000,
        "z_min": -100000,
        "z_max": 100000,
        "theta_min": 0,
        "theta_max": 360,
        "f_min": -100000,
        "f_max": 100000,
    },
    "zoom": {
        "hardware": {"type": "Synthetic", "servo_id": 0},
        "position": {"1x": 0},
        "pixel_size": {"1x": 1.0},
    },
    "shutter": {
        "hardware": {
            "type": "Synthetic",
            "channel": "Synthetic/port0/line0",
        }
    },
    "laser": [
        {
            "wavelength": 488,
            "onoff": {"hardware": {"type": "Synthetic"}},
            "power": {"hardware": {"type": "Synthetic"}},
        }
    ],
}
REQUIRED_STAGE_AXES = ("x", "y", "z", "theta", "f")


class ConfigurationPreloader:
    """Normalize, validate, and safely repair the shared Navigate configuration."""

    def __init__(
        self,
        manager: multiprocessing.Manager,
        policy: Union[PreloadPolicy, str] = PreloadPolicy.SYNTHETIC_FALLBACK,
    ) -> None:
        self.manager = manager
        self.policy = PreloadPolicy(policy)
        self.issues: list[ValidationIssue] = []
        self.schemas = DeviceSchemaResolver()

    def preload(self, configuration: dict) -> PreloadResult:
        """Prepare ``configuration`` in place while preserving Manager proxies."""
        self._ensure_top_level_structure(configuration)
        self._raise_if_strict_errors()
        self.normalize_legacy_configuration(configuration)
        self._ensure_required_devices(configuration)
        self._raise_if_strict_errors()
        verify_configuration(self.manager, configuration)
        self._validate_hardware(configuration)
        self._raise_if_strict_errors()
        verify_configuration(self.manager, configuration)
        verify_experiment_config(self.manager, configuration)
        verify_waveform_constants(self.manager, configuration)
        return PreloadResult(configuration=configuration, issues=self.issues)

    def _raise_if_strict_errors(self) -> None:
        errors = [issue for issue in self.issues if issue.severity == "error"]
        if errors and self.policy == PreloadPolicy.STRICT:
            raise ConfigurationValidationError(errors)

    def _ensure_top_level_structure(self, configuration: dict) -> None:
        required_sections = {
            "configuration": {"microscopes": {"Synthetic Microscope": {}}},
            "experiment": {},
            "waveform_constants": {},
            "gui": {},
        }
        for name, default in required_sections.items():
            if name in configuration and hasattr(configuration[name], "keys"):
                continue
            self._issue(
                name,
                f"Top-level {name} section is missing or has an invalid format.",
                "inserted an empty section",
            )
            if self.policy == PreloadPolicy.SYNTHETIC_FALLBACK:
                update_config_dict(self.manager, configuration, name, default)
            elif self.policy == PreloadPolicy.STRICT:
                self.issues[-1] = ValidationIssue(
                    "error", name, self.issues[-1].message
                )
        configuration_section = configuration.get("configuration")
        if (
            not hasattr(configuration_section, "keys")
            or "microscopes" not in configuration_section
            or not hasattr(configuration_section["microscopes"], "keys")
            or not configuration_section["microscopes"]
        ):
            self._issue(
                "configuration.microscopes",
                "No valid microscopes are configured.",
                "inserted a synthetic microscope",
            )
            if self.policy == PreloadPolicy.SYNTHETIC_FALLBACK:
                update_config_dict(
                    self.manager,
                    configuration["configuration"],
                    "microscopes",
                    {"Synthetic Microscope": {}},
                )
            elif self.policy == PreloadPolicy.STRICT:
                self.issues[-1] = ValidationIssue(
                    "error", "configuration.microscopes", self.issues[-1].message
                )

    def normalize_legacy_configuration(self, configuration: dict) -> None:
        """Apply supported historical key and device-type migrations in place."""
        support_deceased_configuration(configuration)

    def _ensure_required_devices(self, configuration: dict) -> None:
        microscopes = configuration["configuration"]["microscopes"]
        for microscope_name, microscope in microscopes.items():
            for device_name, synthetic_device in REQUIRED_DEVICE_DEFAULTS.items():
                if device_name in microscope and self._has_expected_shape(
                    device_name, microscope[device_name]
                ):
                    continue
                path = f"microscopes.{microscope_name}.{device_name}"
                problem = (
                    "is missing"
                    if device_name not in microscope
                    else "has an invalid format"
                )
                self._issue(
                    path,
                    f"Required {device_name} {problem}.",
                    "added synthetic device",
                )
                if self.policy == PreloadPolicy.SYNTHETIC_FALLBACK:
                    update_config_dict(
                        self.manager, microscope, device_name, synthetic_device
                    )
                elif self.policy == PreloadPolicy.STRICT:
                    self.issues[-1] = ValidationIssue(
                        "error", path, self.issues[-1].message
                    )
            if self._has_expected_shape("stage", microscope.get("stage")):
                self._add_missing_stage_serial_numbers(microscope_name, microscope)
                self._add_missing_stage_axes(microscope_name, microscope)

    def _add_missing_stage_serial_numbers(
        self, microscope_name: str, microscope: dict
    ) -> None:
        stage_hardware = microscope["stage"]["hardware"]
        for index, stage in enumerate(stage_hardware):
            serial_number = stage.get("serial_number")
            if serial_number is not None and str(serial_number).strip():
                continue
            generated_serial_number = f"MISSING-STAGE-{microscope_name}-{index}"
            path = f"microscopes.{microscope_name}.stage.hardware[{index}]"
            self._issue(
                path,
                "Stage serial number is missing.",
                f"added serial number {generated_serial_number}",
            )
            if self.policy == PreloadPolicy.SYNTHETIC_FALLBACK:
                stage["serial_number"] = generated_serial_number
            elif self.policy == PreloadPolicy.STRICT:
                self.issues[-1] = ValidationIssue(
                    "error", path, self.issues[-1].message
                )

    def _add_missing_stage_axes(self, microscope_name: str, microscope: dict) -> None:
        stage_configuration = microscope["stage"]
        stage_hardware = stage_configuration["hardware"]
        configured_axes = set()
        for stage in stage_hardware:
            axes = stage.get("axes", [])
            if isinstance(axes, str):
                axes = [axis.strip() for axis in axes.split(",")]
            configured_axes.update(axis for axis in axes if axis)
        missing_axes = [
            axis for axis in REQUIRED_STAGE_AXES if axis not in configured_axes
        ]
        if not missing_axes:
            return
        path = f"microscopes.{microscope_name}.stage"
        self._issue(
            path,
            "Stage configuration is missing axes: " + ", ".join(missing_axes) + ".",
            "added synthetic stage for missing axes",
        )
        if self.policy == PreloadPolicy.STRICT:
            self.issues[-1] = ValidationIssue("error", path, self.issues[-1].message)
            return
        if self.policy != PreloadPolicy.SYNTHETIC_FALLBACK:
            return
        synthetic_stage = {
            "type": "Synthetic",
            "serial_number": f"SYNTHETIC-STAGE-{len(stage_hardware)}",
            "axes": missing_axes,
        }
        stage_hardware.append(None)
        build_nested_dict(
            self.manager,
            stage_hardware,
            len(stage_hardware) - 1,
            synthetic_stage,
        )
        defaults = REQUIRED_DEVICE_DEFAULTS["stage"]
        for axis in missing_axes:
            for suffix in ("min", "max"):
                key = f"{axis}_{suffix}"
                if key not in stage_configuration:
                    stage_configuration[key] = defaults[key]

    @staticmethod
    def _has_expected_shape(device_name: str, device: Any) -> bool:
        if device_name in {"galvo", "laser"}:
            return isinstance(device, (list, ListProxy)) and bool(device)
        if device_name == "stage":
            return (
                hasattr(device, "keys")
                and "hardware" in device
                and isinstance(device["hardware"], (list, ListProxy))
                and bool(device["hardware"])
            )
        return hasattr(device, "keys")

    def _validate_hardware(self, configuration: dict) -> None:
        microscopes = configuration["configuration"]["microscopes"]
        for microscope_name, microscope in microscopes.items():
            for category in REQUIRED_DEVICE_DEFAULTS:
                if category not in microscope:
                    continue
                devices = microscope[category]
                if category in {"galvo", "laser"}:
                    for index, device in enumerate(devices):
                        self._validate_device(
                            microscope,
                            microscope_name,
                            category,
                            device,
                            index,
                        )
                elif category == "stage":
                    for index, hardware in enumerate(devices["hardware"]):
                        self._validate_device(
                            microscope,
                            microscope_name,
                            category,
                            devices,
                            index,
                            hardware,
                        )
                else:
                    self._validate_device(
                        microscope, microscope_name, category, devices, None
                    )

    def _validate_device(
        self,
        microscope: dict,
        microscope_name: str,
        category: str,
        device: dict,
        index: Optional[int],
        hardware: Optional[dict] = None,
    ) -> None:
        hardware = hardware or device.get("hardware", {})
        validation_device = device
        if category == "stage":
            validation_device = dict(device)
            validation_device["hardware"] = hardware
        device_type = hardware.get("type", "")
        schema = self.schemas.get_schema(category, str(device_type))
        invalid = not schema and device_type.lower() != "synthetic"
        details = "unknown device type" if invalid else ""
        for name, spec in schema.items():
            if not isinstance(spec, SchemaSettingSpec):
                continue
            value = self._schema_value(category, validation_device, name)
            if not self._value_is_valid(category, name, value, spec):
                invalid = True
                details = f"invalid required setting {name}"
                break
        if not invalid:
            return
        path = f"microscopes.{microscope_name}.{category}"
        if index is not None:
            path = f"{path}[{index}]"
        self._issue(
            path, f"{category} has {details}.", "replaced with synthetic device"
        )
        if self.policy == PreloadPolicy.SYNTHETIC_FALLBACK:
            self._replace_with_synthetic(microscope, category, index)
        elif self.policy == PreloadPolicy.STRICT:
            self.issues[-1] = ValidationIssue("error", path, self.issues[-1].message)

    def _replace_with_synthetic(
        self, microscope: dict, category: str, index: Optional[int]
    ) -> None:
        synthetic_device = REQUIRED_DEVICE_DEFAULTS[category]
        if index is None:
            update_config_dict(self.manager, microscope, category, synthetic_device)
            return
        if category == "stage":
            build_nested_dict(
                self.manager,
                microscope[category]["hardware"],
                index,
                synthetic_device["hardware"][0],
            )
            return
        build_nested_dict(
            self.manager, microscope[category], index, synthetic_device[0]
        )

    @staticmethod
    def _schema_value(category: str, device: dict, name: str) -> Any:
        path = name
        if category == "stage" and name in {
            "axes",
            "axes_mapping",
            "feedback_alignment",
        }:
            path = f"hardware/{name}"
        elif "/" not in name and name in {
            "port",
            "baudrate",
            "timeout",
            "serial_number",
        }:
            path = f"hardware/{name}"
        value: Any = device
        for part in path.split("/"):
            if not hasattr(value, "keys") or part not in value:
                return None
            value = value[part]
        return value

    @staticmethod
    def _value_is_valid(
        category: str, name: str, value: Any, spec: SchemaSettingSpec
    ) -> bool:
        if value is None:
            return not spec.required
        if isinstance(value, str) and not value.strip():
            return not spec.required
        if category == "stage" and name in {"axes", "axes_mapping", "joystick_axes"}:
            return bool(value)
        if name == "serial_number":
            return isinstance(value, (int, str)) and bool(str(value).strip())
        if spec.value_type is float and isinstance(value, (int, float)):
            value_is_type = not isinstance(value, bool)
        else:
            value_is_type = isinstance(value, spec.value_type)
        if not value_is_type:
            return False
        if spec.choices is not None and value not in spec.choices:
            return False
        if spec.minimum is not None and value < spec.minimum:
            return False
        if spec.maximum is not None and value > spec.maximum:
            return False
        return True

    def _issue(self, path: str, message: str, action_taken: str) -> None:
        self.issues.append(ValidationIssue("warning", path, message, action_taken))
        logger.warning("Configuration preloader: %s (%s)", message, path)


def preload_configuration(
    manager: multiprocessing.Manager,
    configuration: dict,
    policy: Union[PreloadPolicy, str] = PreloadPolicy.SYNTHETIC_FALLBACK,
) -> PreloadResult:
    """Run Navigate's configuration preloading pipeline on shared dictionaries.

    ``configuration`` remains the original nested ``Manager`` proxy structure;
    no plain-dictionary conversion is performed.
    """
    return ConfigurationPreloader(manager, policy).preload(configuration)
