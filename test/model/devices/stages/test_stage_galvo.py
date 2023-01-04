# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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
#

# Standard Library Imports
import unittest
from pathlib import Path

# Third Party Imports

# Local Imports
from aslm.model.devices.stages.stage_galvo import GalvoNIStage
from aslm.model.dummy import DummyModel

class TestStageGalvo(unittest.TestCase):
    r"""Unit Test for StageBase Class"""

    def test_stage_attributes(self):
        dummy_model = DummyModel()
        microscope_name = 'Mesoscale'
        stage = GalvoNIStage(microscope_name, None, dummy_model.configuration)

        assert hasattr(stage, 'x_pos')
        assert hasattr(stage, 'y_pos')
        assert hasattr(stage, 'z_pos')
        assert hasattr(stage, 'f_pos')
        assert hasattr(stage, 'theta_pos')
        assert hasattr(stage, 'position_dict')
        assert hasattr(stage, 'x_max')
        assert hasattr(stage, 'y_max')
        assert hasattr(stage, 'z_max')
        assert hasattr(stage, 'f_max')
        assert hasattr(stage, 'x_min')
        assert hasattr(stage, 'y_min')
        assert hasattr(stage, 'z_min')
        assert hasattr(stage, 'f_min')
        assert hasattr(stage, 'theta_min')
        assert hasattr(stage, 'create_position_dict') and \
               callable(getattr(stage, 'create_position_dict'))

if __name__ == '__main__':
    unittest.main()