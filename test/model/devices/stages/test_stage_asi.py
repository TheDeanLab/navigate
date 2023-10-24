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
from aslm.model.devices.stages.stage_asi import ASIStage
from aslm.model.devices.APIs.asi.asi_tiger_controller import TigerController


class MockASIStage:
    def __init__(self, ignore_obj):
        self.axes = ["X", "Y", "Z", "M", "N"]
        self.is_open = False
        self.input_buffer = []
        self.output_buffer = []
        self.ignore_obj = ignore_obj

        for axis in self.axes:
            setattr(self, f"{axis}_abs", 0)

    def open(self):
        self.is_open = True

    def reset_input_buffer(self):
        self.input_buffer = []

    def reset_output_buffer(self):
        self.output_buffer = []

    def write(self, command):
        command = command.decode(encoding="ascii")[:-1]
        temps = command.split()
        command = temps[0]
        if command == "WHERE":
            axes = temps[1:]
            pos = [":A"]
            for axis in self.axes:
                if axis not in axes:
                    continue
                pos.append(str(getattr(self, f"{axis}_abs")))
            self.output_buffer.append(" ".join(pos))
        elif command == "MOVE":
            success = True
            for i in range(1, len(temps)):
                axis, pos = temps[i].split("=")
                if axis in self.axes:
                    setattr(self, f"{axis}_abs", float(pos))
                else:
                    success = False
            if success:
                self.output_buffer.append(":A")
            else:
                self.output_buffer.append(":N")

        elif command == "/":
            self.output_buffer.append(":A")
        elif command == "HALT":
            self.output_buffer.append(":A")
        elif command == "SPEED":
            self.output_buffer.append(":A")
        elif command == "BU":
            axes = " ".join(self.axes)
            self.output_buffer.append(
                f"TIGER_COMM\rMotor Axes: {axes} 0 1\rAxis Addr: 1 1 2 2 8 8\rHex "
                "Addr: 31 31 32 32 39 39\rAxis Props: 10 10 0 0 0 0"
            )
        elif command == "AA":
            self.output_buffer.append(":A")
        elif command == "AZ":
            self.output_buffer.append(":A")
        elif command == "B":
            self.output_buffer.append(":A")
        elif command == "PC":
            self.output_buffer.append(":A")
        elif command == "E":
            self.output_buffer.append(":A")

    def readline(self):
        return bytes(self.output_buffer.pop(0), encoding="ascii")

    def __getattr__(self, __name: str):
        return self.ignore_obj


@pytest.fixture
def asi_serial_device(ignore_obj):
    return MockASIStage(ignore_obj)


class TestStageASI:
    """Unit Test for ASI Stage Class"""

    @pytest.fixture(autouse=True)
    def setup_class(
        self,
        stage_configuration,
        asi_serial_device,
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
        self.stage_configuration["stage"]["hardware"]["type"] = "ASI"
        self.asi_serial_device = asi_serial_device
        self.random_single_axis_test = random_single_axis_test
        self.random_multiple_axes_test = random_multiple_axes_test

    def build_device_connection(self):
        port = self.stage_configuration["stage"]["hardware"]["port"]
        baudrate = self.stage_configuration["stage"]["hardware"]["baudrate"]

        asi_stage = TigerController(port, baudrate)
        asi_stage.serial_port = self.asi_serial_device
        asi_stage.connect_to_serial()
        return asi_stage

    def test_stage_attributes(self):
        stage = ASIStage(self.microscope_name, None, self.configuration)

        # Methods
        assert hasattr(stage, "get_position_dict") and callable(
            getattr(stage, "get_position_dict")
        )
        assert hasattr(stage, "report_position") and callable(
            getattr(stage, "report_position")
        )
        assert hasattr(stage, "move_axis_absolute") and callable(
            getattr(stage, "move_axis_absolute")
        )
        assert hasattr(stage, "move_absolute") and callable(
            getattr(stage, "move_absolute")
        )
        assert hasattr(stage, "stop") and callable(getattr(stage, "stop"))
        assert hasattr(stage, "get_abs_position") and callable(
            getattr(stage, "get_abs_position")
        )

    @pytest.mark.parametrize(
        "axes, axes_mapping",
        [
            (["x"], None),
            (["y"], None),
            (["x", "z"], None),
            (["f", "z"], None),
            (["x", "y", "z"], None),
            (["x", "y", "z", "f"], None),
            (["x"], ["Y"]),
            (["y"], ["Z"]),
            (["x", "z"], ["X", "Y"]),
            (["f", "z"], ["M", "X"]),
            (["x", "y", "z"], ["Y", "X", "M"]),
            (["x", "y", "z", "f"], ["X", "M", "Y", "Z"]),
            (["x", "y", "z", "f"], ["x", "M", "y", "Z"]),
        ],
    )
    def test_initialize_stage(self, axes, axes_mapping):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        stage = ASIStage(self.microscope_name, None, self.configuration)

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
            # using default mapping which is hard coded in stage_pi.py
            default_mapping = {"x": "Z", "y": "Y", "z": "X", "f": "M"}
            for axis, device_axis in stage.axes_mapping.items():
                assert default_mapping[axis] == device_axis
            assert len(stage.axes_mapping) <= len(stage.axes)
        else:
            for i, axis in enumerate(axes):
                assert stage.axes_mapping[axis] == axes_mapping[i].upper()

        assert stage.stage_limits is True

    @pytest.mark.parametrize(
        "axes, axes_mapping",
        [
            (["x"], None),
            (["y"], None),
            (["x", "z"], None),
            (["f", "z"], None),
            (["x", "y", "z"], None),
            (["x", "y", "z", "f"], None),
            (["x"], ["Y"]),
            (["y"], ["Z"]),
            (["x", "z"], ["X", "Y"]),
            (["f", "z"], ["M", "X"]),
            (["x", "y", "z"], ["Y", "X", "M"]),
            (["x", "y", "z", "f"], ["X", "M", "Y", "Z"]),
            (["x", "y", "z", "f"], ["x", "M", "y", "Z"]),
        ],
    )
    def test_report_position(self, axes, axes_mapping):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        self.configuration["configuration"]["microscopes"][self.microscope_name][
            "zoom"
        ] = {}
        self.configuration["configuration"]["microscopes"][self.microscope_name][
            "zoom"
        ]["pixel_size"] = {"5X": 1.3}
        asi_stage = self.build_device_connection()
        stage = ASIStage(self.microscope_name, asi_stage, self.configuration)

        for _ in range(10):
            pos_dict = {}
            for axis in axes:
                pos = random.randrange(-100, 500)
                pos_dict[f"{axis}_pos"] = float(pos)
                if axis == "theta":
                    setattr(
                        asi_stage.serial_port,
                        f"{stage.axes_mapping[axis]}_abs",
                        pos * 1000.0,
                    )
                else:
                    setattr(
                        asi_stage.serial_port,
                        f"{stage.axes_mapping[axis]}_abs",
                        pos * 10.0,
                    )
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
            (["x", "y", "z", "f"], None),
            (["x"], ["Y"]),
            (["y"], ["Z"]),
            (["x", "z"], ["X", "Y"]),
            (["f", "z"], ["M", "X"]),
            (["x", "y", "z"], ["Y", "X", "M"]),
            (["x", "y", "z", "f"], ["X", "M", "Y", "Z"]),
            (["x", "y", "z", "f"], ["x", "M", "y", "Z"]),
        ],
    )
    def test_move_axis_absolute(self, axes, axes_mapping):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        asi_stage = self.build_device_connection()
        stage = ASIStage(self.microscope_name, asi_stage, self.configuration)
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
            (["x", "y", "z", "f"], None),
            (["x"], ["Y"]),
            (["y"], ["Z"]),
            (["x", "z"], ["X", "Y"]),
            (["f", "z"], ["M", "X"]),
            (["x", "y", "z"], ["Y", "X", "M"]),
            (["x", "y", "z", "f"], ["X", "M", "Y", "Z"]),
            (["x", "y", "z", "f"], ["x", "M", "y", "Z"]),
        ],
    )
    def test_move_absolute(self, axes, axes_mapping):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = axes_mapping
        asi_stage = self.build_device_connection()
        stage = ASIStage(self.microscope_name, asi_stage, self.configuration)
        self.random_multiple_axes_test(stage)
        stage.stage_limits = False
        self.random_multiple_axes_test(stage)
