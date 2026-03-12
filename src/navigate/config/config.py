# Copyright (c) 2021-2025  The University of Texas Southwestern Medical Center.
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
import time
import shutil
import platform
from pathlib import Path
from os.path import isfile
import multiprocessing
from multiprocessing.managers import ListProxy, DictProxy
import logging
from typing import Union

# Third Party Imports
import yaml

# Local Imports
from navigate.tools.common_functions import build_ref_name, load_param_from_module
from navigate.tools.file_functions import save_yaml_file

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


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
        "frames_to_average": 1,
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
        for k in ["databuffer_size", "number_of_pixels", "frames_to_average"]:
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
        configuration["configuration"]["microscopes"][microscope_name]["filter_wheel"]
    )
    filterwheel_list = [
        list(filter_wheel_config["available_filters"].keys())
        for filter_wheel_config in configuration["configuration"]["microscopes"][
            microscope_name
        ]["filter_wheel"]
    ]
    prefix = "channel_"
    channel_nums = configuration["configuration"]["gui"]["channels"]["count"]
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
            if channel_value[k] < 0:
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
    other_constants_dict = {
        "remote_focus_settle_duration": "0",
        "percent_smoothing": "0",
        "remote_focus_delay": "0",
        "remote_focus_ramp_falling": "5",
        "camera_settle_duration": "0",
        "camera_delay": configuration["configuration"]["microscopes"][microscope_name][
            "camera"
        ]["delay"],
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

    channel_count = 5
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
        # camera
        # delay_percent -> delay
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
        if "delay" not in camera_config.keys():
            camera_config["delay"] = camera_config.get("delay_percent", 2)

        try:
            channel_count = max(channel_count, camera_config.get("count", 5))
        except TypeError:
            channel_count = 5

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
            filter_wheel_idx = build_ref_name(
                "-",
                filter_wheel_config["hardware"]["type"],
                filter_wheel_config["hardware"]["wheel_number"],
            )
            if filter_wheel_idx not in ref_list["filter_wheel"]:
                ref_list["filter_wheel"].append(filter_wheel_idx)
                filter_wheel_seq.append(filter_wheel_config)
                if (
                    filter_wheel_config.get("name", None) is None
                    and filter_wheel_config.get("hardware", {}).get("name", None)
                    is not None
                ):
                    filter_wheel_config["name"] = filter_wheel_config["hardware"][
                        "name"
                    ]
            idx = ref_list["filter_wheel"].index(filter_wheel_idx)
            if filter_wheel_seq[idx].get("name", None):
                filter_wheel_config["name"] = filter_wheel_seq[idx]["name"]
            elif filter_wheel_config.get("name", None):
                filter_wheel_seq[idx]["name"] = filter_wheel_config["name"]
            elif filter_wheel_config.get("hardware", {}).get("name", None):
                filter_wheel_seq[idx]["name"] = filter_wheel_config["hardware"]["name"]
            if filter_wheel_seq[idx].get("name", None):
                if filter_wheel_seq[idx]["name"] not in filter_wheel_names:
                    filter_wheel_names.add(filter_wheel_seq[idx]["name"])
                else:
                    filter_wheel_seq[idx]["name"] = None

    # make sure all filter wheel entries have hardware name
    for i, filter_wheel_config in enumerate(filter_wheel_seq):
        if filter_wheel_config.get("name", None) is None:
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

    update_config_dict(
        manager,
        configuration["configuration"],
        "gui",
        {"channels": {"count": channel_count}},
    )


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
            stage_config = microscope_config["stage"]["hardware"]
            if type(stage_config) is not ListProxy:
                stage_config = [stage_config]
            for stage in stage_config:
                if stage["type"] in deceased_device_type_names:
                    stage["type"] = deceased_device_type_names[stage["type"]]
                    is_updated = True
