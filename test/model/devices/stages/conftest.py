"""Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
# """

# Standard Library Imports
import random

# Third Party Imports
import pytest


@pytest.fixture(scope="module")
def stage_configuration():
    return {
        "stage": {
            "hardware": {
                "name": "stage",
                "type": "",
                "port": "COM10",
                "baudrate": 115200,
                "serial_number": 123456,
                "axes": ["x", "y", "z", "f", "theta"],
            },
            "x_max": 100,
            "x_min": -10,
            "y_max": 200,
            "y_min": -20,
            "z_max": 300,
            "z_min": -30,
            "f_max": 400,
            "f_min": -40,
            "theta_max": 360,
            "theta_min": 0,
        }
    }


@pytest.fixture
def random_single_axis_test(stage_configuration):
    pos_sequence = []
    for _ in range(10):
        axis = random.choice(["x", "y", "z", "theta", "f"])
        # random valid pos
        axis_min = stage_configuration["stage"][f"{axis}_min"]
        axis_max = stage_configuration["stage"][f"{axis}_max"]
        pos = random.randrange(axis_min, axis_max)
        pos_sequence.append((axis, pos))

    for _ in range(10):
        # valid and non-valid pos
        axis = random.choice(["x", "y", "z", "theta", "f"])
        pos = random.randrange(-100, 500)
        pos_sequence.append((axis, pos))

    def _verify_move_axis_absolute(stage):
        axes_mapping = stage.axes_mapping

        stage_pos = stage.report_position()
        for axis, pos in pos_sequence:
            stage.move_axis_absolute(axis, pos, True)
            temp_pos = stage.report_position()
            axis_min = stage_configuration["stage"][f"{axis}_min"]
            axis_max = stage_configuration["stage"][f"{axis}_max"]
            if axis in axes_mapping:
                if not stage.stage_limits or (pos >= axis_min and pos <= axis_max):
                    stage_pos[f"{axis}_pos"] = pos
            assert stage_pos == temp_pos

    return _verify_move_axis_absolute


@pytest.fixture
def random_multiple_axes_test(stage_configuration):
    pos_sequence = []
    axes = ["x", "y", "z", "f", "theta"]
    for _ in range(20):
        pos = {}
        for axis in axes:
            pos[axis] = random.randrange(-100, 500)
        pos_sequence.append(pos)

    def _verify_move_absolute(stage):
        axes_mapping = stage.axes_mapping

        # move one axis inside supported axes
        stage_pos = stage.report_position()
        for pos_dict in pos_sequence:
            axis = random.choice(list(axes_mapping.keys()))
            pos = pos_dict[axis]
            axis_min = stage_configuration["stage"][f"{axis}_min"]
            axis_max = stage_configuration["stage"][f"{axis}_max"]
            move_dict = {f"{axis}_abs": pos}
            stage.move_absolute(move_dict)
            temp_pos = stage.report_position()
            if not stage.stage_limits or (pos >= axis_min and pos <= axis_max):
                stage_pos[f"{axis}_pos"] = pos
            assert stage_pos == temp_pos

        # move all axes inside supported axes
        stage_pos = stage.report_position()
        for pos_dict in pos_sequence:
            move_dict = {}
            for axis in axes_mapping.keys():
                move_dict[f"{axis}_abs"] = pos_dict[axis]

            stage.move_absolute(move_dict)
            temp_pos = stage.report_position()
            for axis in axes_mapping:
                pos = pos_dict[axis]
                axis_min = stage_configuration["stage"][f"{axis}_min"]
                axis_max = stage_configuration["stage"][f"{axis}_max"]
                if not stage.stage_limits or (pos >= axis_min and pos <= axis_max):
                    stage_pos[f"{axis}_pos"] = pos
            assert stage_pos == temp_pos

        # move all axes (including supported axes and non-supported axes)
        stage_pos = stage.report_position()
        for pos_dict in pos_sequence:
            move_dict = dict(
                map(lambda axis: (f"{axis}_abs", pos_dict[axis]), pos_dict)
            )
            stage.move_absolute(move_dict)
            temp_pos = stage.report_position()
            for axis in axes_mapping:
                pos = pos_dict[axis]
                axis_min = stage_configuration["stage"][f"{axis}_min"]
                axis_max = stage_configuration["stage"][f"{axis}_max"]
                if not stage.stage_limits or (pos >= axis_min and pos <= axis_max):
                    stage_pos[f"{axis}_pos"] = pos
            assert stage_pos == temp_pos

    return _verify_move_absolute
