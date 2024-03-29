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
import time
import shutil
import platform
from pathlib import Path
from os.path import isfile
from multiprocessing.managers import ListProxy, DictProxy

# Third Party Imports
import yaml

# Local Imports


def get_navigate_path():
    """Establish a program home directory in AppData/Local/.navigate for Windows
    or ~/.navigate for Mac and Linux.

    Returns
    -------
    str
        Path to Navigate home directory.

    Examples
    --------
    >>> get_navigate_path()
    'C:\\Users\\username\\AppData\\Local\\.navigate'
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
    """
    navigate_directory = get_navigate_path()
    if not os.path.exists(navigate_directory):
        os.mkdir(navigate_directory)
    configuration_directory = Path(os.path.join(navigate_directory, "config"))
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
    new_config : dict or str
        Dictionary values or
        yaml file name

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
    if type(configuration["experiment"]) is not DictProxy:
        update_config_dict(manager, configuration, "experiment", {})

    # verify/build autofocus parameter setting
    # get autofocus supported devices(stages, remote_focus) from configuration.yaml file
    device_dict = {}
    # get devices: stages, NI remote_focus_device
    device_config = configuration["configuration"]["microscopes"]
    for microscope_name in device_config.keys():
        microscope_config = device_config[microscope_name]
        device_dict[microscope_name] = {}
        if (
            "remote_focus_device" in microscope_config.keys()
            and microscope_config["remote_focus_device"]["hardware"]["type"] == "NI"
        ):
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
        "robust_fit": False,
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

    # if root directory/saving direcotry doesn't exist
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
    camera_setting_dict = configuration["experiment"]["CameraParameters"]
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

    # sensor mode
    if camera_setting_dict["sensor_mode"] not in ["Normal", "Light-Sheet"]:
        camera_setting_dict["sensor_mode"] = "Normal"
    if camera_setting_dict["readout_direction"] not in [
        "Top-to-Bottom",
        "Bottom-to-Top",
        "Bidirectional",
        "Rev. Bidirectional"
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
        "multiposition_count": 1,
        "selected_channels": 0,
        "stack_z_origin": 0,
        "stack_focus_origin": 0,
        "start_focus": 0.0,
        "end_focus": 0.0,
        "abs_z_start": 0.0,
        "abs_z_end": 100.0,
        "scanrange": 500.0,
        "n_plane": 1.0,
        "offset_start": 0.0,
        "offset_end": 9.8,
        "conpro_cycling_mode": "per_stack",
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
            "lasers"
        ]
    ]
    filterwheel_list = list(
        configuration["configuration"]["microscopes"][microscope_name]["filter_wheel"][
            "available_filters"
        ].keys()
    )
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
        if channel_value["filter"] not in filterwheel_list:
            channel_value["filter"] = filterwheel_list[0]
        channel_value["filter_position"] = filterwheel_list.index(
            channel_value["filter"]
        )
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

    microscope_setting_dict["selected_channels"] = selected_channel_num

    # MultiPositions
    if (
        "MultiPositions" not in configuration["experiment"]
        or type(configuration["experiment"]["MultiPositions"]) is not ListProxy
    ):
        update_config_dict(manager, configuration["experiment"], "MultiPositions", [])
    position_ids = []
    multipositions = configuration["experiment"]["MultiPositions"]
    for i, position in enumerate(multipositions):
        for axis in ["x", "y", "z", "theta", "f"]:
            try:
                position[axis] = float(position[axis])
            except ValueError:
                position_ids.append(i)
                break
    for idx in position_ids[::-1]:
        del multipositions[idx]
    if len(multipositions) < 1:
        multipositions.append(None)
        update_config_dict(
            manager,
            multipositions,
            0,
            {"x": 10.0, "y": 10.0, "z": 10.0, "f": 10.0, "theta": 10.0},
        )
    microscope_setting_dict["multiposition_count"] = len(multipositions)


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

        # get lasers
        lasers = []
        for laser in config_dict["lasers"]:
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
                            "amplitude": config_dict["remote_focus_device"][
                                "amplitude"
                            ],
                            "offset": config_dict["remote_focus_device"]["offset"],
                            # "percent_smoothing": "0",
                            # "delay": config_dict["remote_focus_device"][
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
                            waveform_dict[microscope_name][zoom][laser][
                                k
                            ] = config_dict["remote_focus_device"].get(k, "0")
                        else:
                            try:
                                float(waveform_dict[microscope_name][zoom][laser][k])
                            except ValueError:
                                waveform_dict[microscope_name][zoom][laser][
                                    k
                                ] = config_dict["remote_focus_device"].get(k, "0")

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

            for zoom in config_dict["zoom"]["position"].keys():
                if (
                    zoom not in waveform_dict[microscope_name].keys()
                    or type(waveform_dict[microscope_name][zoom]) is not DictProxy
                ):
                    update_config_dict(
                        manager,
                        waveform_dict[microscope_name],
                        zoom,
                        {
                            "amplitude": "0.11",
                            "offset": config_dict["galvo"][i]["offset"],
                            "frequency": config_dict["galvo"][i]["frequency"],
                        },
                    )
                else:
                    for k in ["amplitude", "offset", "frequency"]:
                        if k not in waveform_dict[microscope_name][zoom].keys():
                            waveform_dict[microscope_name][zoom][k] = config_dict[
                                "galvo"
                            ][i].get(k, "0")
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
    other_constants_dict = {
        "remote_focus_settle_duration": "0",
        "percent_smoothing": "0",
        "remote_focus_delay": config_dict["remote_focus_device"][
            "delay"
        ],
        "remote_focus_ramp_falling": config_dict["remote_focus_device"][
            "ramp_falling"
        ]
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
            waveform_dict["other_constants"][k] = "0"

def verify_configuration(manager, configuration):
    """Verify configuration files.
    
    Supports old version of configurations.
    """
    device_config = configuration["configuration"]["microscopes"]
    for microscope_name in device_config.keys():
        # camera
        # delay_percent -> delay
        camera_config = device_config[microscope_name]["camera"]
        if "delay" not in camera_config.keys():
            camera_config["delay"] = camera_config.get("delay_percent", 2)
        # remote focus
        # ramp_falling_percent -> ramp_falling
        remote_focus_config = device_config[microscope_name]["remote_focus_device"]
        if "ramp_falling" not in remote_focus_config.keys():
            remote_focus_config["ramp_falling"] = remote_focus_config.get("ramp_falling_percent", 5)
        if "delay" not in remote_focus_config.keys():
            remote_focus_config["delay"] = remote_focus_config.get("delay_percent", 0)
