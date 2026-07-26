# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
#

import random
import copy
from contextlib import contextmanager

import pytest
import numpy as np
from unittest.mock import patch


@pytest.fixture
def channels_tab_controller(dummy_controller):
    from navigate.controller.sub_controllers.channels_tab import (
        ChannelsTabController,
    )

    return ChannelsTabController(
        dummy_controller.view.settings.channels_tab, dummy_controller
    )


@contextmanager
def stage_limit_settings(channels_tab_controller, **limits):
    configuration = channels_tab_controller.parent_controller.configuration
    configuration_controller = (
        channels_tab_controller.parent_controller.configuration_controller
    )
    microscope_name = configuration_controller.microscope_name
    stage_config = configuration["configuration"]["microscopes"][microscope_name][
        "stage"
    ]
    stage_parameters = configuration["experiment"]["StageParameters"]
    original_limits = {key: stage_config.get(key) for key in limits}
    original_limit_flag = stage_parameters.get("limits", True)
    try:
        for key, value in limits.items():
            stage_config[key] = value
        yield
    finally:
        for key, value in original_limits.items():
            stage_config[key] = value
        stage_parameters["limits"] = original_limit_flag


def assert_spinbox_range(widget, from_value, to_value):
    assert float(widget.cget("from")) == from_value
    assert float(widget.cget("to")) == to_value


def test_launch_tiling_wizard_rejects_invalid_camera_fov(channels_tab_controller):
    from tkinter import messagebox

    main_controller = channels_tab_controller.parent_controller

    with (
        patch.object(
            main_controller,
            "camera_setting_controller",
            create=True,
        ) as camera_setting_controller,
        patch.object(
            camera_setting_controller,
            "calculate_physical_dimensions",
            return_value=False,
        ) as calculate_physical_dimensions,
        patch.object(messagebox, "showwarning") as showwarning,
        patch(
            "navigate.controller.sub_controllers.channels_tab.TilingWizardPopup"
        ) as tiling_wizard_popup,
        patch(
            "navigate.controller.sub_controllers.channels_tab.TilingWizardController"
        ),
    ):
        channels_tab_controller.launch_tiling_wizard()

    calculate_physical_dimensions.assert_called_once_with()
    showwarning.assert_called_once()
    tiling_wizard_popup.assert_not_called()
    assert not hasattr(channels_tab_controller, "tiling_wizard_controller")


def test_launch_tiling_wizard_accepts_valid_camera_fov(channels_tab_controller):
    main_controller = channels_tab_controller.parent_controller

    with (
        patch.object(
            main_controller,
            "camera_setting_controller",
            create=True,
        ) as camera_setting_controller,
        patch.object(
            camera_setting_controller,
            "calculate_physical_dimensions",
            return_value=True,
        ) as calculate_physical_dimensions,
        patch(
            "navigate.controller.sub_controllers.channels_tab.TilingWizardPopup"
        ) as tiling_wizard_popup,
        patch(
            "navigate.controller.sub_controllers.channels_tab.TilingWizardController"
        ) as tiling_wizard_controller,
    ):
        channels_tab_controller.launch_tiling_wizard()

    calculate_physical_dimensions.assert_called_once_with()
    tiling_wizard_popup.assert_called_once()
    tiling_wizard_controller.assert_called_once()
    assert (
        channels_tab_controller.tiling_wizard_controller
        is tiling_wizard_controller.return_value
    )


@pytest.mark.parametrize(
    "origin, expected_range",
    [
        (0, (0, 200)),
        (100, (-100, 100)),
    ],
)
def test_stack_position_limits_follow_stage_limits_for_z_axis(
    channels_tab_controller, origin, expected_range
):
    with stage_limit_settings(
        channels_tab_controller, z_min=0, z_max=200, f_min=-100000, f_max=100000
    ):
        channels_tab_controller.parent_controller.configuration["experiment"][
            "StageParameters"
        ]["limits"] = True
        channels_tab_controller.z_origin = origin
        channels_tab_controller.focus_origin = 0

        channels_tab_controller.set_spinbox_range_limits(
            channels_tab_controller.parent_controller.configuration["gui"]
        )

        for widget_name in ["start_position", "end_position"]:
            assert_spinbox_range(
                channels_tab_controller.stack_acq_widgets[widget_name].widget,
                expected_range[0],
                expected_range[1],
            )


def test_stack_position_limits_follow_stage_limits_for_focus_axis(
    channels_tab_controller,
):
    with stage_limit_settings(
        channels_tab_controller, z_min=-100000, z_max=100000, f_min=10, f_max=50
    ):
        channels_tab_controller.parent_controller.configuration["experiment"][
            "StageParameters"
        ]["limits"] = True
        channels_tab_controller.z_origin = 0
        channels_tab_controller.focus_origin = 20

        channels_tab_controller.set_spinbox_range_limits(
            channels_tab_controller.parent_controller.configuration["gui"]
        )

        for widget_name in ["start_focus", "end_focus"]:
            assert_spinbox_range(
                channels_tab_controller.stack_acq_widgets[widget_name].widget,
                -10,
                30,
            )


def test_stack_position_limits_fall_back_to_gui_config_when_stage_limits_disabled(
    channels_tab_controller,
):
    with stage_limit_settings(channels_tab_controller, z_min=0, z_max=200):
        configuration = channels_tab_controller.parent_controller.configuration
        configuration["experiment"]["StageParameters"]["limits"] = False

        channels_tab_controller.set_spinbox_range_limits(configuration["gui"])

        stack_config = configuration["gui"]["stack_acquisition"]
        assert_spinbox_range(
            channels_tab_controller.stack_acq_widgets["start_position"].widget,
            stack_config["z_start_pos"]["min"],
            stack_config["z_start_pos"]["max"],
        )
        assert_spinbox_range(
            channels_tab_controller.stack_acq_widgets["end_position"].widget,
            stack_config["z_end_pos"]["min"],
            stack_config["z_end_pos"]["max"],
        )


def test_verify_experiment_values_rejects_out_of_range_stack_position(
    channels_tab_controller,
):
    with stage_limit_settings(
        channels_tab_controller, z_min=0, z_max=200, f_min=-100000, f_max=100000
    ):
        configuration = channels_tab_controller.parent_controller.configuration
        configuration["experiment"]["StageParameters"]["limits"] = True
        channels_tab_controller.microscope_state_dict = configuration["experiment"][
            "MicroscopeState"
        ]
        channels_tab_controller.channel_setting_controller.channel_setting_dict = (
            channels_tab_controller.microscope_state_dict["channels"]
        )
        channels_tab_controller.z_origin = 100
        channels_tab_controller.focus_origin = 0
        channels_tab_controller.microscope_state_dict["image_mode"] = "z-stack"
        channels_tab_controller.microscope_state_dict["number_z_steps"] = 1
        channels_tab_controller.stack_acq_vals["number_z_steps"].set(1)
        channels_tab_controller.microscope_state_dict["timepoints"] = 1
        channels_tab_controller.microscope_state_dict["stack_pause"] = 0
        channels_tab_controller.microscope_state_dict["start_position"] = -101
        channels_tab_controller.microscope_state_dict["end_position"] = 0
        channels_tab_controller.microscope_state_dict["start_focus"] = 0
        channels_tab_controller.microscope_state_dict["end_focus"] = 0

        warning = channels_tab_controller.verify_experiment_values()

        assert "start_position is outside the z stage limits" in warning


def test_update_z_steps(channels_tab_controller):
    # Calculate params
    z_start, f_start = random.randint(1, 1000), random.randint(1, 1000)
    z_end, f_end = random.randint(1, 1000), random.randint(1, 1000)
    if z_end < z_start:
        # Sort so we are always going low to high
        tmp = z_start
        tmp_f = f_start
        z_start = z_end
        f_start = f_end
        z_end = tmp
        f_end = tmp_f
    step_size = max(1, min(random.randint(1, 10), (z_end - z_start) // 2))

    # Set params
    channels_tab_controller.microscope_state_dict = (
        channels_tab_controller.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]
    )
    channels_tab_controller.in_initialization = False
    channels_tab_controller.stack_acq_vals["start_position"].set(z_start)
    channels_tab_controller.stack_acq_vals["start_focus"].set(f_start)
    channels_tab_controller.stack_acq_vals["end_position"].set(z_end)
    channels_tab_controller.stack_acq_vals["end_focus"].set(f_end)
    channels_tab_controller.stack_acq_vals["step_size"].set(step_size)

    # Run
    channels_tab_controller.update_z_steps()

    # Verify
    number_z_steps = int(np.ceil(np.abs((z_start - z_end) / step_size)))
    assert (
        int(channels_tab_controller.stack_acq_vals["number_z_steps"].get())
        == number_z_steps
    )

    # test flip_z is True
    microscope_name = (
        channels_tab_controller.parent_controller.configuration_controller.microscope_name
    )
    stage_config = channels_tab_controller.parent_controller.configuration[
        "configuration"
    ]["microscopes"][microscope_name]["stage"]
    stage_config["flip_z"] = True
    channels_tab_controller.z_origin = (z_start + z_end) / 2
    channels_tab_controller.stack_acq_vals["start_position"].set(z_end)
    channels_tab_controller.stack_acq_vals["start_focus"].set(f_end)
    channels_tab_controller.stack_acq_vals["end_position"].set(z_start)
    channels_tab_controller.stack_acq_vals["end_focus"].set(f_start)
    channels_tab_controller.update_z_steps()
    assert channels_tab_controller.stack_acq_vals["step_size"].get() == step_size
    assert channels_tab_controller.microscope_state_dict["step_size"] == -1 * step_size
    assert (
        channels_tab_controller.stack_acq_vals["number_z_steps"].get() == number_z_steps
    )
    stage_config["flip_z"] = False


def test_update_start_position(channels_tab_controller):
    z, f = random.randint(0, 1000), random.randint(0, 1000)
    channels_tab_controller.parent_controller.configuration["experiment"][
        "StageParameters"
    ]["z"] = z
    channels_tab_controller.parent_controller.configuration["experiment"][
        "StageParameters"
    ]["f"] = f

    channels_tab_controller.update_start_position()

    assert channels_tab_controller.z_origin == z
    assert channels_tab_controller.focus_origin == f
    assert int(channels_tab_controller.stack_acq_vals["start_position"].get()) == 0
    assert int(channels_tab_controller.stack_acq_vals["start_focus"].get()) == 0

    # test flip_z is True
    microscope_name = (
        channels_tab_controller.parent_controller.configuration_controller.microscope_name
    )
    stage_config = channels_tab_controller.parent_controller.configuration[
        "configuration"
    ]["microscopes"][microscope_name]["stage"]
    stage_config["flip_z"] = True
    channels_tab_controller.update_start_position()

    assert channels_tab_controller.z_origin == z
    assert channels_tab_controller.focus_origin == f
    assert int(channels_tab_controller.stack_acq_vals["end_position"].get()) == 0
    assert int(channels_tab_controller.stack_acq_vals["end_focus"].get()) == 0
    stage_config["flip_z"] = False


def test_update_end_position(channels_tab_controller):
    configuration = channels_tab_controller.parent_controller.configuration

    # Initialize
    z, f = random.randint(0, 1000), random.randint(0, 1000)
    z_shift, f_shift = random.randint(1, 500), random.randint(1, 500)
    configuration["experiment"]["StageParameters"]["z"] = z + z_shift
    configuration["experiment"]["StageParameters"]["f"] = f + f_shift

    print(f"z: {z} z-shift: {z_shift} f: {f} f-shift: {f_shift}")
    print(f'z-dict: {configuration["experiment"]["StageParameters"]["z"]}')
    print(f'f-dict: {configuration["experiment"]["StageParameters"]["f"]}')

    # Step backwards and record results
    channels_tab_controller.z_origin = z - z_shift
    channels_tab_controller.focus_origin = f - f_shift
    channels_tab_controller.update_end_position()
    z_origin_minus = copy.deepcopy(channels_tab_controller.z_origin)
    f_origin_minus = copy.deepcopy(channels_tab_controller.focus_origin)
    start_position_minus = copy.deepcopy(
        channels_tab_controller.stack_acq_vals["start_position"].get()
    )
    end_position_minus = copy.deepcopy(
        channels_tab_controller.stack_acq_vals["end_position"].get()
    )
    start_focus_minus = copy.deepcopy(
        channels_tab_controller.stack_acq_vals["start_focus"].get()
    )
    end_focus_minus = copy.deepcopy(
        channels_tab_controller.stack_acq_vals["end_focus"].get()
    )

    print("back")
    print(f"z: {z} z-shift: {z_shift} f: {f} f-shift: {f_shift}")
    print(f'z-dict: {configuration["experiment"]["StageParameters"]["z"]}')
    print(f'f-dict: {configuration["experiment"]["StageParameters"]["f"]}')

    # Step forward
    configuration["experiment"]["StageParameters"]["z"] = z - z_shift
    configuration["experiment"]["StageParameters"]["f"] = f - f_shift
    channels_tab_controller.z_origin = z + z_shift
    channels_tab_controller.focus_origin = f + f_shift
    channels_tab_controller.update_end_position()

    print("forward")
    print(f"z: {z} z-shift: {z_shift} f: {f} f-shift: {f_shift}")
    print(f'z-dict: {configuration["experiment"]["StageParameters"]["z"]}')
    print(f'f-dict: {configuration["experiment"]["StageParameters"]["f"]}')

    # Ensure we achieve the same origin
    assert channels_tab_controller.z_origin == z_origin_minus
    assert channels_tab_controller.focus_origin == f_origin_minus
    assert (
        channels_tab_controller.stack_acq_vals["start_position"].get()
        == start_position_minus
    )
    assert (
        channels_tab_controller.stack_acq_vals["end_position"].get()
        == end_position_minus
    )
    assert (
        channels_tab_controller.stack_acq_vals["start_focus"].get() == start_focus_minus
    )
    assert channels_tab_controller.stack_acq_vals["end_focus"].get() == end_focus_minus

    # test flip_z is True
    microscope_name = (
        channels_tab_controller.parent_controller.configuration_controller.microscope_name
    )
    stage_config = channels_tab_controller.parent_controller.configuration[
        "configuration"
    ]["microscopes"][microscope_name]["stage"]
    stage_config["flip_z"] = True
    # forward
    channels_tab_controller.z_origin = z
    channels_tab_controller.focus_origin = f
    configuration["experiment"]["StageParameters"]["z"] = z - 2 * z_shift
    configuration["experiment"]["StageParameters"]["f"] = f - 2 * f_shift
    channels_tab_controller.update_end_position()
    assert channels_tab_controller.z_origin == z - z_shift
    assert channels_tab_controller.focus_origin == f - f_shift
    assert channels_tab_controller.stack_acq_vals["start_position"].get() == z_shift
    assert channels_tab_controller.stack_acq_vals["end_position"].get() == -1 * z_shift
    assert channels_tab_controller.stack_acq_vals["start_focus"].get() == f_shift
    assert channels_tab_controller.stack_acq_vals["end_focus"].get() == -1 * f_shift

    # backward
    channels_tab_controller.z_origin = z
    channels_tab_controller.focus_origin = f
    configuration["experiment"]["StageParameters"]["z"] = z + 2 * z_shift
    configuration["experiment"]["StageParameters"]["f"] = f + 2 * f_shift
    channels_tab_controller.update_end_position()
    assert channels_tab_controller.z_origin == z + z_shift
    assert channels_tab_controller.focus_origin == f + f_shift
    assert channels_tab_controller.stack_acq_vals["start_position"].get() == z_shift
    assert channels_tab_controller.stack_acq_vals["end_position"].get() == -1 * z_shift
    assert channels_tab_controller.stack_acq_vals["start_focus"].get() == f_shift
    assert channels_tab_controller.stack_acq_vals["end_focus"].get() == -1 * f_shift
    stage_config["flip_z"] = False


def test_update_start_update_end_position(channels_tab_controller):
    configuration = channels_tab_controller.parent_controller.configuration
    channels_tab_controller.microscope_state_dict = configuration["experiment"][
        "MicroscopeState"
    ]
    channels_tab_controller.in_initialization = False

    # Initialize
    z, f = random.randint(0, 1000), random.randint(0, 1000)
    z_shift, f_shift = random.randint(1, 500), random.randint(1, 500)
    configuration["experiment"]["StageParameters"]["z"] = z - z_shift
    configuration["experiment"]["StageParameters"]["f"] = f - f_shift
    channels_tab_controller.update_start_position()

    print(f"z: {z} z-shift: {z_shift} f: {f} f-shift: {f_shift}")
    print(f'z-dict: {configuration["experiment"]["StageParameters"]["z"]}')
    print(f'f-dict: {configuration["experiment"]["StageParameters"]["f"]}')

    # Step forward and record results
    configuration["experiment"]["StageParameters"]["z"] = z + z_shift
    configuration["experiment"]["StageParameters"]["f"] = f + f_shift
    channels_tab_controller.update_end_position()
    z_origin_minus = copy.deepcopy(channels_tab_controller.z_origin)
    f_origin_minus = copy.deepcopy(channels_tab_controller.focus_origin)
    start_position_minus = copy.deepcopy(
        channels_tab_controller.stack_acq_vals["start_position"].get()
    )
    end_position_minus = copy.deepcopy(
        channels_tab_controller.stack_acq_vals["end_position"].get()
    )
    start_focus_minus = copy.deepcopy(
        channels_tab_controller.stack_acq_vals["start_focus"].get()
    )
    end_focus_minus = copy.deepcopy(
        channels_tab_controller.stack_acq_vals["end_focus"].get()
    )

    print("back")
    print(f"z: {z} z-shift: {z_shift} f: {f} f-shift: {f_shift}")
    print(f'z-dict: {configuration["experiment"]["StageParameters"]["z"]}')
    print(f'f-dict: {configuration["experiment"]["StageParameters"]["f"]}')

    channels_tab_controller.update_start_position()

    # Step back
    configuration["experiment"]["StageParameters"]["z"] = z - z_shift
    configuration["experiment"]["StageParameters"]["f"] = f - f_shift
    channels_tab_controller.update_end_position()

    print("forward")
    print(f"z: {z} z-shift: {z_shift} f: {f} f-shift: {f_shift}")
    print(f'z-dict: {configuration["experiment"]["StageParameters"]["z"]}')
    print(f'f-dict: {configuration["experiment"]["StageParameters"]["f"]}')

    # Ensure we achieve the same origin
    assert channels_tab_controller.z_origin == z_origin_minus
    assert channels_tab_controller.focus_origin == f_origin_minus
    assert (
        channels_tab_controller.stack_acq_vals["start_position"].get()
        == start_position_minus
    )
    assert (
        channels_tab_controller.stack_acq_vals["end_position"].get()
        == end_position_minus
    )
    assert (
        channels_tab_controller.stack_acq_vals["start_focus"].get() == start_focus_minus
    )
    assert channels_tab_controller.stack_acq_vals["end_focus"].get() == end_focus_minus

    # test flip_z is true
    microscope_name = (
        channels_tab_controller.parent_controller.configuration_controller.microscope_name
    )
    stage_config = channels_tab_controller.parent_controller.configuration[
        "configuration"
    ]["microscopes"][microscope_name]["stage"]
    stage_config["flip_z"] = True
    configuration = channels_tab_controller.parent_controller.configuration
    z, f = random.randint(0, 1000), random.randint(0, 1000)
    z_shift, f_shift = random.randint(1, 500), random.randint(1, 500)
    configuration["experiment"]["StageParameters"]["z"] = z - z_shift
    configuration["experiment"]["StageParameters"]["f"] = f - f_shift
    channels_tab_controller.update_start_position()
    configuration["experiment"]["StageParameters"]["z"] = z + z_shift
    configuration["experiment"]["StageParameters"]["f"] = f + f_shift
    channels_tab_controller.update_end_position()

    assert channels_tab_controller.z_origin == z
    assert channels_tab_controller.focus_origin == f
    assert channels_tab_controller.stack_acq_vals["start_position"].get() == z_shift
    assert channels_tab_controller.stack_acq_vals["end_position"].get() == -1 * z_shift
    assert channels_tab_controller.stack_acq_vals["start_focus"].get() == f_shift
    assert channels_tab_controller.stack_acq_vals["end_focus"].get() == -1 * f_shift

    assert configuration["experiment"]["MicroscopeState"]["start_position"] == z_shift
    assert (
        configuration["experiment"]["MicroscopeState"]["end_position"] == -1 * z_shift
    )
    assert configuration["experiment"]["MicroscopeState"]["abs_z_start"] == z - z_shift
    assert configuration["experiment"]["MicroscopeState"]["abs_z_end"] == z + z_shift
    assert configuration["experiment"]["MicroscopeState"]["start_focus"] == f_shift
    assert configuration["experiment"]["MicroscopeState"]["end_focus"] == -1 * f_shift

    configuration["experiment"]["StageParameters"]["z"] = z + z_shift
    configuration["experiment"]["StageParameters"]["f"] = f + f_shift
    channels_tab_controller.update_start_position()
    configuration["experiment"]["StageParameters"]["z"] = z - z_shift
    configuration["experiment"]["StageParameters"]["f"] = f - f_shift
    channels_tab_controller.update_end_position()

    assert channels_tab_controller.z_origin == z
    assert channels_tab_controller.focus_origin == f
    assert channels_tab_controller.stack_acq_vals["start_position"].get() == z_shift
    assert channels_tab_controller.stack_acq_vals["end_position"].get() == -1 * z_shift
    assert channels_tab_controller.stack_acq_vals["start_focus"].get() == f_shift
    assert channels_tab_controller.stack_acq_vals["end_focus"].get() == -1 * f_shift

    assert configuration["experiment"]["MicroscopeState"]["start_position"] == z_shift
    assert (
        configuration["experiment"]["MicroscopeState"]["end_position"] == -1 * z_shift
    )
    assert configuration["experiment"]["MicroscopeState"]["abs_z_start"] == z - z_shift
    assert configuration["experiment"]["MicroscopeState"]["abs_z_end"] == z + z_shift
    assert configuration["experiment"]["MicroscopeState"]["start_focus"] == f_shift
    assert configuration["experiment"]["MicroscopeState"]["end_focus"] == -1 * f_shift
    stage_config["flip_z"] = False


@pytest.mark.parametrize("is_multiposition", [True, False])
def test_toggle_multiposition(channels_tab_controller, is_multiposition):
    channels_tab_controller.populate_experiment_values()
    channels_tab_controller.is_multiposition_val.set(is_multiposition)
    with patch.object(channels_tab_controller, "update_timepoint_setting") as uts:
        channels_tab_controller.toggle_multiposition()
        assert channels_tab_controller.is_multiposition == is_multiposition
        assert (
            channels_tab_controller.microscope_state_dict["is_multiposition"]
            == is_multiposition
        )
        uts.assert_called()
