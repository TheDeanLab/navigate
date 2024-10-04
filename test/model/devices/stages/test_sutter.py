# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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
from navigate.model.devices.stages.sutter import SutterStage
from navigate.model.devices.APIs.sutter.MP285 import MP285


class MockMP285Stage:
    def __init__(self, ignore_obj):
        self.axes = ["x", "y", "z"]
        for axis in self.axes:
            setattr(self, f"{axis}_abs", 0)
        self.input_buffer = []
        self.output_buffer = []
        self.in_waiting = 0
        self.ignore_obj = ignore_obj

    def open(self):
        pass

    def reset_input_buffer(self):
        self.input_buffer = []

    def reset_output_buffer(self):
        self.output_buffer = []

    def write(self, command):
        if command == bytes.fromhex("63") + bytes.fromhex("0d"):
            # get current x, y, and z position
            self.output_buffer.append(
                self.x_abs.to_bytes(4, byteorder="little", signed=True)
                + self.y_abs.to_bytes(4, byteorder="little", signed=True)
                + self.z_abs.to_bytes(4, byteorder="little", signed=True)
                + bytes.fromhex("0d")
            )
            self.in_waiting += 13
        elif (
            command[0] == int("6d", 16)
            and len(command) == 14
            and command[-1] == int("0d", 16)
        ):
            # move x, y, and z to specific position
            self.x_abs = int.from_bytes(command[1:5], byteorder="little", signed=True)
            self.y_abs = int.from_bytes(command[5:9], byteorder="little", signed=True)
            self.z_abs = int.from_bytes(command[9:13], byteorder="little", signed=True)
            self.output_buffer.append(bytes.fromhex("0d"))
            self.in_waiting += 1
        elif (
            command[0] == int("56", 16)
            and len(command) == 4
            and command[-1] == int("0d", 16)
        ):
            # set resolution and velocity
            self.output_buffer.append(bytes.fromhex("0d"))
            self.in_waiting += 1
        elif command[0] == int("03", 16) and len(command) == 1:
            # interrupt move
            self.output_buffer.append(bytes.fromhex("0d"))
            self.in_waiting += 1
        elif command == bytes.fromhex("61") + bytes.fromhex("0d"):
            # set absolute mode
            self.output_buffer.append(bytes.fromhex("0d"))
            self.in_waiting += 1
        elif command == bytes.fromhex("62") + bytes.fromhex("0d"):
            # set relative mode
            self.in_waiting += 1
            self.output_buffer.append(bytes.fromhex("0d"))

    def read_until(self, expected, size=100):
        return self.output_buffer.pop(0)

    def read(self, byte_num=1):
        self.in_waiting -= len(self.output_buffer[0])
        return self.output_buffer.pop(0)

    def __getattr__(self, __name: str):
        return self.ignore_obj


@pytest.fixture
def mp285_serial_device(ignore_obj):
    return MockMP285Stage(ignore_obj)


class TestStageSutter:
    """Unit Test for StageBase Class"""

    @pytest.fixture(autouse=True)
    def setup_class(
        self,
        stage_configuration,
        mp285_serial_device,
        random_single_axis_test,
        random_multiple_axes_test,
    ):
        self.microscope_name = "Mesoscale"
        self.configuration = {
            "configuration": {
                "microscopes": {self.microscope_name: stage_configuration}
            }
        }
        self.stage_configuration = stage_configuration
        self.stage_configuration["stage"]["hardware"]["type"] = "MP285"
        self.mp285_serial_device = mp285_serial_device
        self.random_single_axis_test = random_single_axis_test
        self.random_multiple_axes_test = random_multiple_axes_test

    def build_device_connection(self):
        port = self.stage_configuration["stage"]["hardware"]["port"]
        baudrate = self.stage_configuration["stage"]["hardware"]["baudrate"]
        timeout = 5.0

        mp285 = MP285(port, baudrate, timeout)
        mp285.serial = self.mp285_serial_device
        mp285.connect_to_serial()
        return mp285

    def test_stage_attributes(self):
        stage = SutterStage(
            self.microscope_name, self.build_device_connection(), self.configuration
        )

        # Methods
        assert hasattr(stage, "get_position_dict") and callable(
            getattr(stage, "get_position_dict")
        )
        assert hasattr(stage, "report_position") and callable(
            getattr(stage, "report_position")
        )
        assert hasattr(stage, "move_absolute") and callable(
            getattr(stage, "move_absolute")
        )
        assert hasattr(stage, "stop") and callable(getattr(stage, "stop"))

    @pytest.mark.parametrize(
        "axes, axes_mapping",
        [
            (["x"], None),
            (["y"], None),
            (["x", "z"], None),
            (["f", "z"], None),
            (["x", "y", "z"], None),
            (["x"], ["y"]),
            (["y"], ["z"]),
            (["x", "z"], ["y", "z"]),
            (["f", "z"], ["x", "z"]),
            (["x", "y", "z"], ["y", "z", "x"]),
        ],
    )
    def test_initialize_stage(self, axes, axes_mapping):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        stage = SutterStage(
            self.microscope_name, self.build_device_connection(), self.configuration
        )

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
            # using default mapping which is hard coded in sutter.py
            default_mapping = {"x": "x", "y": "y", "z": "z"}
            for axis, device_axis in stage.axes_mapping.items():
                assert default_mapping[axis] == device_axis
            assert len(stage.axes_mapping) <= len(stage.axes)
        else:
            for i, axis in enumerate(axes):
                assert stage.axes_mapping[axis] == axes_mapping[i]

        assert stage.stage_limits is True

    @pytest.mark.parametrize(
        "axes, axes_mapping",
        [
            (["x"], None),
            (["y"], None),
            (["x", "z"], None),
            (["f", "z"], None),
            (["x", "y", "z"], None),
            (["x"], ["y"]),
            (["y"], ["z"]),
            (["x", "z"], ["y", "z"]),
            (["f", "z"], ["x", "z"]),
            (["x", "y", "z"], ["y", "z", "x"]),
        ],
    )
    def test_report_position(self, axes, axes_mapping):
        mp285_stage = self.build_device_connection()
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        stage = SutterStage(self.microscope_name, mp285_stage, self.configuration)
        for _ in range(10):
            pos_dict = {}
            for axis in axes:
                pos = random.randrange(-100, 500)
                if axis in stage.axes_mapping:
                    pos_dict[f"{axis}_pos"] = pos * 0.04
                    setattr(mp285_stage.serial, f"{stage.axes_mapping[axis]}_abs", pos)
                else:
                    pos_dict[f"{axis}_pos"] = 0
            temp_pos = stage.report_position()
            assert pos_dict == temp_pos

    @pytest.mark.parametrize(
        "axes, axes_mapping",
        [
            (["x"], None),
            (["y"], None),
            (["x", "z"], None),
            (["f", "z"], None),
            (["x", "y", "z"], None),
            (["x"], ["y"]),
            (["y"], ["z"]),
            (["x", "z"], ["y", "z"]),
            (["f", "z"], ["x", "z"]),
            (["x", "y", "z"], ["y", "z", "x"]),
        ],
    )
    def test_move_axis_absolute(self, axes, axes_mapping):
        mp285_stage = self.build_device_connection()
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        stage = SutterStage(self.microscope_name, mp285_stage, self.configuration)
        self.random_single_axis_test(stage)
        stage.stage_limits = False
        self.random_single_axis_test(stage)

    @pytest.mark.parametrize(
        "axes, axes_mapping",
        [
            (["x"], None),
            (["y"], None),
            (["x", "z"], None),
            (["f", "z"], None),
            (["x", "y", "z"], None),
            (["x"], ["y"]),
            (["y"], ["z"]),
            (["x", "z"], ["y", "z"]),
            (["f", "z"], ["x", "z"]),
            (["x", "y", "z"], ["y", "z", "x"]),
        ],
    )
    def test_move_absolute(self, axes, axes_mapping):
        mp285_stage = self.build_device_connection()
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        stage = SutterStage(self.microscope_name, mp285_stage, self.configuration)
        self.random_multiple_axes_test(stage)
        stage.stage_limits = False
        self.random_multiple_axes_test(stage)
