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

# Standard Library Imports
import pytest
import random

# Third Party Imports

# Local Imports
from aslm.model.devices.stages.stage_base import StageBase
from aslm.model.dummy import DummyModel


class TestStageBase:
    """Unit Test for StageBase Class"""

    @pytest.fixture(autouse=True)
    def setup_class(self, stage_configuration):
        self.microscope_name = "Mesoscale"
        self.configuration = {
            "configuration": {
                "microscopes": {self.microscope_name: stage_configuration}
            }
        }
        self.stage_configuration = stage_configuration

    @pytest.mark.parametrize(
        "axes, axes_mapping",
        [
            (["x"], None),
            (["y"], None),
            (["x", "z"], None),
            (["f", "z"], None),
            (["x", "y", "z"], None),
            (["x", "y", "z", "f"], None),
            (["x", "y", "z", "f", "theta"], None),
            (["x"], [1]),
            (["y"], [2]),
            (["x", "z"], [1, 3]),
            (["f", "z"], [2, 3]),
            (["x", "y", "z"], [1, 2, 3]),
            (["x", "y", "z", "f"], [1, 3, 2, 4]),
            (["x", "y", "z", "f", "theta"], [3, 5, 2, 1, 4]),
        ],
    )
    def test_stage_attributes(self, axes, axes_mapping):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        stage = StageBase(self.microscope_name, None, self.configuration)

        # Attributes
        for axis in axes:
            assert hasattr(stage, f"{axis}_pos")
            assert hasattr(stage, f"{axis}_min")
            assert hasattr(stage, f"{axis}_max")
            assert getattr(stage, f"{axis}_pos") == 0
            assert (
                getattr(stage, f"{axis}_min")
                == self.stage_configuration["stage"][f"{axis}_min"]
            )
            assert (
                getattr(stage, f"{axis}_max")
                == self.stage_configuration["stage"][f"{axis}_max"]
            )

        if axes_mapping is None:
            assert stage.axes_mapping == {}
        else:
            for i, axis in enumerate(axes):
                assert stage.axes_mapping[axis] == axes_mapping[i]

        assert stage.stage_limits == True

    @pytest.mark.parametrize(
        "axes, axes_pos",
        [
            (["x"], [1]),
            (["y"], [2]),
            (["x", "z"], [1, 3]),
            (["f", "z"], [2, 3]),
            (["x", "y", "z"], [1, 2, 3]),
            (["x", "y", "z", "f"], [1, 3, 2, 4]),
            (["x", "y", "z", "f", "theta"], [3, 5, 2, 1, 4]),
        ],
    )
    def test_get_position_dict(self, axes, axes_pos):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        stage = StageBase(self.microscope_name, None, self.configuration)
        for i, axis in enumerate(axes):
            setattr(stage, f"{axis}_pos", axes_pos[i])

        pos_dict = stage.get_position_dict()
        for k, v in pos_dict.items():
            assert getattr(stage, k) == v

    @pytest.mark.parametrize(
        "axes, axes_mapping",
        [
            (["x"], [1]),
            (["y"], [2]),
            (["x", "z"], [1, 3]),
            (["f", "z"], [2, 3]),
            (["x", "y", "z"], [1, 2, 3]),
            (["x", "y", "z", "f"], [1, 3, 2, 4]),
            (["x", "y", "z", "f", "theta"], [3, 5, 2, 1, 4]),
        ],
    )
    def test_get_abs_position(self, axes, axes_mapping):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        stage = StageBase(self.microscope_name, None, self.configuration)

        for axis in axes:
            axis_min = self.stage_configuration["stage"][f"{axis}_min"]
            axis_max = self.stage_configuration["stage"][f"{axis}_max"]
            # axis_abs_position inside the boundaries
            axis_abs = random.randrange(axis_min, axis_max)
            assert stage.get_abs_position(axis, axis_abs) == axis_abs

            # axis_abs_position < axis_min
            axis_abs = axis_min - 10.5
            assert stage.get_abs_position(axis, axis_abs) == -1e50
            # turn off stage_limits
            stage.stage_limits = False
            assert stage.get_abs_position(axis, axis_abs) == axis_abs
            stage.stage_limits = True

            # axis_abs_position > axis_max
            axis_abs = axis_max + 10.5
            assert stage.get_abs_position(axis, axis_abs) == -1e50
            # turn off stage_limits
            stage.stage_limits = False
            assert stage.get_abs_position(axis, axis_abs) == axis_abs
            stage.stage_limits = True

        # axis is not supported
        all_axes = set(["x", "y", "z", "f", "theta"])
        sub_axes = all_axes - set(axes)
        for axis in sub_axes:
            assert stage.get_abs_position(axis, 1.0) == -1e50
            # turn off stage_limits
            stage.stage_limits = False
            assert stage.get_abs_position(axis, axis_abs) == -1e50
            stage.stage_limits = True

    @pytest.mark.parametrize(
        "axes, axes_mapping",
        [
            (["x"], [1]),
            (["y"], [2]),
            (["x", "z"], [1, 3]),
            (["f", "z"], [2, 3]),
            (["x", "y", "z"], [1, 2, 3]),
            (["x", "y", "z", "f"], [1, 3, 2, 4]),
            (["x", "y", "z", "f", "theta"], [3, 5, 2, 1, 4]),
        ],
    )
    def test_verify_abs_position(self, axes, axes_mapping):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        stage = StageBase(self.microscope_name, None, self.configuration)

        move_dict = {}
        abs_dict = {}
        for axis in axes:
            axis_min = self.stage_configuration["stage"][f"{axis}_min"]
            axis_max = self.stage_configuration["stage"][f"{axis}_max"]
            # axis_abs_position inside the boundaries
            axis_abs = random.randrange(axis_min, axis_max)
            move_dict[f"{axis}_abs"] = axis_abs
            abs_dict[axis] = axis_abs

        assert stage.verify_abs_position(move_dict) == abs_dict

        # turn off stage_limits
        stage.stage_limits = False
        axis = random.choice(axes)
        axis_min = self.stage_configuration["stage"][f"{axis}_min"]
        axis_max = self.stage_configuration["stage"][f"{axis}_max"]
        move_dict[f"{axis}_abs"] = axis_min - 1.5
        abs_dict[axis] = axis_min - 1.5
        assert stage.verify_abs_position(move_dict) == abs_dict
        move_dict[f"{axis}_abs"] = axis_max + 1.5
        abs_dict[axis] = axis_max + 1.5
        assert stage.verify_abs_position(move_dict) == abs_dict
        stage.stage_limits = True

        # axis is not included in axes list
        axis_abs = random.randrange(axis_min, axis_max)
        move_dict[f"{axis}_abs"] = axis_abs
        abs_dict[axis] = axis_abs

        move_dict["theta_abs"] = 180
        if "theta" in axes:
            abs_dict["theta"] = 180
        assert stage.verify_abs_position(move_dict) == abs_dict
        stage.stage_limits = False
        assert stage.verify_abs_position(move_dict) == abs_dict

        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping[
            :-1
        ]
        stage = StageBase(self.microscope_name, None, self.configuration)
        abs_dict.pop(axes[-1])

        assert stage.verify_abs_position(move_dict) == abs_dict
        stage.stage_limits = False
        assert stage.verify_abs_position(move_dict) == abs_dict
