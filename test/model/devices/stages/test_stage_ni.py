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
from unittest.mock import patch

# Third Party Imports

# Local Imports
from navigate.model.devices.stages.ni import GalvoNIStage
from test.model.dummy import DummyModel
from navigate.tools.common_functions import copy_proxy_object


class TestStageGalvo:
    """Unit Test for Galvo stage Class"""

    @pytest.fixture(autouse=True)
    def setup_class(
        self,
        stage_configuration,
        ignore_obj,
        random_single_axis_test,
        random_multiple_axes_test,
    ):
        dummy_model = DummyModel()
        self.configuration = copy_proxy_object(dummy_model.configuration)
        self.microscope_name = list(
            self.configuration["configuration"]["microscopes"].keys()
        )[0]
        self.configuration["configuration"]["microscopes"][self.microscope_name][
            "stage"
        ] = stage_configuration["stage"]
        self.stage_configuration = stage_configuration
        self.stage_configuration["stage"]["hardware"]["type"] = "GalvoNIStage"
        self.stage_configuration["stage"]["hardware"]["volts_per_micron"] = "0.1"
        self.stage_configuration["stage"]["hardware"]["max"] = 5.0
        self.stage_configuration["stage"]["hardware"]["min"] = 0.1
        self.stage_configuration["stage"]["hardware"]["axes_mapping"] = ["PXI6259/ao2"]

        self.daq = ignore_obj
        self.random_single_axis_test = random_single_axis_test
        self.random_multiple_axes_test = random_multiple_axes_test

    @patch("nidaqmx.Task")
    def test_stage_attributes(self, *args):
        stage = GalvoNIStage(self.microscope_name, self.daq, self.configuration)

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

    @pytest.mark.parametrize("axes", [(["x"]), (["y"]), (["f"])])
    def test_initialize_stage(self, axes):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        with patch("nidaqmx.Task"):
            stage = GalvoNIStage(self.microscope_name, self.daq, self.configuration)

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

            for i, axis in enumerate(axes):
                assert (
                    stage.axes_mapping[axis]
                    == self.stage_configuration["stage"]["hardware"]["axes_mapping"][i]
                )

    @pytest.mark.parametrize("axes", [(["x"]), (["y"]), (["f"])])
    def test_report_position(self, axes):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        with patch("nidaqmx.Task"):
            stage = GalvoNIStage(self.microscope_name, self.daq, self.configuration)

            for _ in range(10):
                pos_dict = {}
                for axis in axes:
                    pos = random.randrange(-100, 500)
                    pos_dict[f"{axis}_pos"] = float(pos)
                    setattr(stage, f"{axis}_pos", float(pos))
                temp_pos = stage.report_position()
                assert pos_dict == temp_pos

    @pytest.mark.parametrize("axes", [(["x"]), (["y"]), (["f"])])
    def test_move_axis_absolute(self, axes):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        with patch("nidaqmx.Task"):
            stage = GalvoNIStage(self.microscope_name, self.daq, self.configuration)

            self.random_single_axis_test(stage)
            stage.stage_limits = False
            self.random_single_axis_test(stage)

    @pytest.mark.parametrize("axes", [(["x"]), (["y"]), (["f"])])
    def test_move_absolute(self, axes):
        self.stage_configuration["stage"]["hardware"]["axes"] = axes
        with patch("nidaqmx.Task"):
            stage = GalvoNIStage(self.microscope_name, self.daq, self.configuration)

            self.random_multiple_axes_test(stage)
            stage.stage_limits = False
            self.random_multiple_axes_test(stage)
