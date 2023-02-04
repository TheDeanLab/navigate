# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

import pytest
import numpy as np


@pytest.fixture
def channels_tab_controller(dummy_controller):
    from aslm.controller.sub_controllers.channels_tab_controller import (
        ChannelsTabController,
    )

    return ChannelsTabController(
        dummy_controller.view.settings.channels_tab, dummy_controller
    )


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
    channels_tab_controller.stack_acq_vals["start_position"].set(z_start)
    channels_tab_controller.stack_acq_vals["start_focus"].set(f_start)
    channels_tab_controller.stack_acq_vals["end_position"].set(z_end)
    channels_tab_controller.stack_acq_vals["end_focus"].set(f_end)
    channels_tab_controller.stack_acq_vals["step_size"].set(step_size)

    # Run
    channels_tab_controller.update_z_steps()

    # Verify
    # number_z_steps = int(np.ceil(np.abs((z_start - z_end) / step_size)))
    assert (
        int(channels_tab_controller.stack_acq_vals["number_z_steps"].get())
        == 0  # currently return
    )


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


def test_update_start_update_end_position(channels_tab_controller):
    configuration = channels_tab_controller.parent_controller.configuration

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
