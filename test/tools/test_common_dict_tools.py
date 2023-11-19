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

# Third Party Imports

# Local Imports
from aslm.tools.common_dict_tools import update_stage_dict

import unittest
from unittest.mock import MagicMock


def create_mock_target():
    """Create a mock target object (Model or Controller) for testing."""
    target = MagicMock()
    target.configuration = {
        "experiment": {
            "MicroscopeState": {"channels": None},
            "GalvoParameters": {},
            "CameraParameters": {},
        },
        "etl_constants": {"ETLConstants": {"low": {}, "high": {}}},
    }
    return target


def create_mock_stage_target():
    """Create a mock target object (Model or Controller) for testing."""
    target = MagicMock()
    target.configuration = {
        "experiment": {"StageParameters": {"x": None, "y": None, "z": None}}
    }
    return target


class UpdateStageDictTestCase(unittest.TestCase):
    def test_update_single_axis(self):
        target = create_mock_stage_target()
        pos_dict = {"x_position": 10.0}
        update_stage_dict(target, pos_dict)
        self.assertEqual(
            target.configuration["experiment"]["StageParameters"]["x"], 10.0
        )

    def test_update_multiple_axes(self):
        target = create_mock_stage_target()
        pos_dict = {"y_position": 5.0, "z_position": 2.5}
        update_stage_dict(target, pos_dict)
        self.assertEqual(
            target.configuration["experiment"]["StageParameters"]["y"], 5.0
        )
        self.assertEqual(
            target.configuration["experiment"]["StageParameters"]["z"], 2.5
        )

    def test_update_invalid_axis(self):
        target = create_mock_stage_target()
        pos_dict = {"invalid_axis": 3.14}
        update_stage_dict(target, pos_dict)
        self.assertNotIn(
            "invalid_axis", target.configuration["experiment"]["StageParameters"]
        )


if __name__ == "__main__":
    unittest.main()
