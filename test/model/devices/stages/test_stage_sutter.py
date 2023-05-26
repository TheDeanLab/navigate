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
import unittest
import random

# Third Party Imports

# Local Imports
from aslm.model.devices.stages.stage_sutter import SutterStage
from aslm.model.dummy import DummyModel


class TestStageSutter(unittest.TestCase):
    """Unit Test for StageBase Class"""

    def test_stage_attributes(self):
        dummy_model = DummyModel()
        dummy_MP285 = type("MP285", (object,), {})
        dummy_MP285.set_resolution_and_velocity = lambda *args, **kwargs: print("set resolution and velocity")
        dummy_MP285.set_absolute_mode = lambda *args, **kwargs: print("set absolute mode")
        dummy_MP285.get_current_position = lambda *args, **kwargs: (random.random(), random.random(), random.random())
        microscope_name = "Mesoscale"
        

        stage_configuration = {
            "microscopes": {
                microscope_name: {
                    "stage": {
                        "hardware": {
                            "name": "stage",
                            "type": "MP285",
                            "port": "COM10",
                            "baudrate": 115200,
                            "serail_number": 123456,
                            "axes": ["x", "y", "z"],
                        },
                        "x_max": 100,
                        "x_min": -100,
                        "y_max": 200,
                        "y_min": -200,
                        "z_max": 300,
                        "z_min": -300
                    }
                }

            }
        }

        stage = SutterStage(microscope_name=microscope_name,
                            device_connection=dummy_MP285,
                            configuration={"configuration": stage_configuration},
                            device_id=0)

        # Attributes
        for axis in stage_configuration["microscopes"][microscope_name]["stage"]["hardware"]["axes"]:
            assert hasattr(stage, f"{axis}_pos")
            assert hasattr(stage, f"{axis}_min")
            assert hasattr(stage, f"{axis}_max")

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


if __name__ == "__main__":
    unittest.main()
