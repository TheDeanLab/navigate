"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

# Standard Library Imports
import unittest
from pathlib import Path

# Third Party Imports

# Local Imports
from aslm.model.devices.shutter.laser_shutter_synthetic import SyntheticShutter
from aslm.model.aslm_model_config import Session as session


class TestSyntheticShutter(unittest.TestCase):
    r"""Unit Test for SyntheticShutter Class"""

    def test_synthetic_shutter_attributes(self):
        base_directory = Path(__file__).resolve().parent.parent.parent.parent.parent
        configuration_directory = Path.joinpath(base_directory, 'src', 'aslm', 'config')

        configuration_path = Path.joinpath(configuration_directory, 'configuration.yml')
        experiment_path = Path.joinpath(configuration_directory, 'experiment.yml')

        configuration = session(file_path=configuration_path)
        experiment = session(file_path=experiment_path)
        shutter = SyntheticShutter(configuration,
                              experiment)

        # Attributes
        assert hasattr(shutter, 'configuration')
        assert hasattr(shutter, 'experiment')
        assert hasattr(shutter, 'shutter_right')
        assert hasattr(shutter, 'shutter_right_state')
        assert hasattr(shutter, 'shutter_left')
        assert hasattr(shutter, 'shutter_left_state')

        # Methods
        assert hasattr(shutter, 'open_left') and callable(getattr(shutter, 'open_left'))
        assert hasattr(shutter, 'open_right') and callable(getattr(shutter, 'open_right'))
        assert hasattr(shutter, 'close_shutters') and callable(getattr(shutter, 'close_shutters'))
        assert hasattr(shutter, 'state') and callable(getattr(shutter, 'state'))

if __name__ == '__main__':
    unittest.main()
