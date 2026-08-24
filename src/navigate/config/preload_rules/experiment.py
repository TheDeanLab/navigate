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
import os
import time
from multiprocessing.managers import DictProxy, ListProxy

from navigate.config.config import get_navigate_path, update_config_dict
from navigate.config.preload import PreloadContext, PreloadRule


def ensure_experiment_root(context: PreloadContext) -> None:
    """Ensure the experiment section is a shared dictionary."""
    if type(context.configuration["experiment"]) is not DictProxy:
        update_config_dict(context.manager, context.configuration, "experiment", {})


def repair_autofocus_parameters(context: PreloadContext) -> None:
    """Verify/build autofocus parameter settings."""
    manager = context.manager
    configuration = context.configuration
    device_dict = {}
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

    for microscope_name in list(autofocus_setting_dict.keys()):
        if microscope_name not in device_dict:
            autofocus_setting_dict.pop(microscope_name)
        else:
            for device in list(autofocus_setting_dict[microscope_name].keys()):
                if device not in device_dict[microscope_name]:
                    autofocus_setting_dict[microscope_name].pop(device)
                else:
                    for device_ref in list(
                        autofocus_setting_dict[microscope_name][device].keys()
                    ):
                        if (
                            device_ref
                            not in autofocus_setting_dict[microscope_name][device]
                        ):
                            autofocus_setting_dict[microscope_name][device].pop(
                                device_ref
                            )


def repair_saving_settings(context: PreloadContext) -> None:
    """Verify/build experiment saving settings."""
    manager = context.manager
    configuration = context.configuration
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

    if not os.path.exists(saving_setting_dict["root_directory"]):
        saving_setting_dict["root_directory"] = saving_dict_sample["root_directory"]
    if not os.path.exists(saving_setting_dict["save_directory"]):
        saving_setting_dict["save_directory"] = saving_dict_sample["save_directory"]


def repair_camera_parameters(context: PreloadContext) -> None:
    """Verify/build experiment camera parameters."""
    manager = context.manager
    configuration = context.configuration
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
        if camera_setting_dict["binning"] not in ["1x1", "2x2", "4x4"]:
            camera_setting_dict["binning"] = "1x1"
        try:
            camera_setting_dict["x_pixels"] = int(camera_setting_dict["x_pixels"])
        except ValueError:
            camera_setting_dict["x_pixels"] = camera_parameters_dict_sample["x_pixels"]

        try:
            camera_setting_dict["y_pixels"] = int(camera_setting_dict["y_pixels"])
        except ValueError:
            camera_setting_dict["y_pixels"] = camera_parameters_dict_sample["y_pixels"]

        if camera_setting_dict["x_pixels"] <= 0:
            camera_setting_dict["x_pixels"] = camera_parameters_dict_sample["x_pixels"]
        if camera_setting_dict["y_pixels"] <= 0:
            camera_setting_dict["y_pixels"] = camera_parameters_dict_sample["y_pixels"]
        x_binning = int(camera_setting_dict["binning"][0])
        y_binning = int(camera_setting_dict["binning"][2])
        camera_setting_dict["img_x_pixels"] = (
            camera_setting_dict["x_pixels"] // x_binning
        )
        camera_setting_dict["img_y_pixels"] = (
            camera_setting_dict["y_pixels"] // y_binning
        )
        if camera_setting_dict["is_centered"]:
            camera_setting_dict["center_x"] = camera_setting_dict["x_pixels"] // 2
            camera_setting_dict["center_y"] = camera_setting_dict["y_pixels"] // 2

        if camera_setting_dict["sensor_mode"] not in ["Normal", "Light-Sheet"]:
            camera_setting_dict["sensor_mode"] = "Normal"
        if camera_setting_dict["readout_direction"] not in [
            "Top-to-Bottom",
            "Bottom-to-Top",
            "Bidirectional",
            "Rev. Bidirectional",
        ]:
            camera_setting_dict["readout_direction"] = "Top-to-Bottom"

        for k in ["databuffer_size", "number_of_pixels"]:
            try:
                camera_setting_dict[k] = int(camera_setting_dict[k])
            except ValueError:
                camera_setting_dict[k] = camera_parameters_dict_sample[k]
            if camera_setting_dict[k] < 1:
                camera_setting_dict[k] = camera_parameters_dict_sample[k]


def repair_stage_parameters(context: PreloadContext) -> None:
    """Verify/build experiment stage parameters."""
    manager = context.manager
    configuration = context.configuration
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


def repair_microscope_state(context: PreloadContext) -> None:
    """Verify/build experiment microscope state defaults."""
    manager = context.manager
    configuration = context.configuration
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

    if (
        microscope_setting_dict["microscope_name"]
        not in configuration["configuration"]["microscopes"].keys()
    ):
        microscope_setting_dict["microscope_name"] = microscope_name
    microscope_name = microscope_setting_dict["microscope_name"]
    if (
        microscope_setting_dict["zoom"]
        not in configuration["configuration"]["microscopes"][microscope_name]["zoom"][
            "position"
        ].keys()
    ):
        microscope_setting_dict["zoom"] = configuration["configuration"]["microscopes"][
            microscope_name
        ]["zoom"]["position"].keys()[0]


def repair_channel_settings(context: PreloadContext) -> None:
    """Verify experiment channel settings against microscope devices."""
    manager = context.manager
    configuration = context.configuration
    microscope_setting_dict = configuration["experiment"]["MicroscopeState"]
    microscope_name = microscope_setting_dict["microscope_name"]
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
    for channel in list(channel_setting_dict.keys()):
        if not channel.startswith(prefix):
            del channel_setting_dict[channel]
            continue
        channel_id = int(channel[len(prefix) :]) - 1
        if channel_id < 0 or channel_id >= channel_nums:
            del channel_setting_dict[channel]
            continue
        channel_value = channel_setting_dict[channel]
        if channel_value["laser"] not in laser_list:
            channel_value["laser"] = laser_list[0]
        channel_value["laser_index"] = laser_list.index(channel_value["laser"])
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
        if (
            "is_selected" not in channel_value.keys()
            or type(channel_value["is_selected"]) != bool
        ):
            channel_value["is_selected"] = False
        if channel_value["is_selected"]:
            selected_channel_num += 1
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


EXPERIMENT_RULES = [
    PreloadRule("experiment", "root", ensure_experiment_root),
    PreloadRule("experiment", "autofocus_parameters", repair_autofocus_parameters),
    PreloadRule("experiment", "saving_settings", repair_saving_settings),
    PreloadRule("experiment", "camera_parameters", repair_camera_parameters),
    PreloadRule("experiment", "stage_parameters", repair_stage_parameters),
    PreloadRule("experiment", "microscope_state", repair_microscope_state),
    PreloadRule("experiment", "channel_settings", repair_channel_settings),
]
