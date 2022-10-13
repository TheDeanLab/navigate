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

# Third Party Imports

# Local Imports
from aslm.model.dummy import DummyModel


class TestSyntheticHardware(unittest.TestCase):
    dummy_model = DummyModel()
    microscope_name = 'microscope_low_res'

    def test_synthetic_daq(self):
        from aslm.model.devices.daq.daq_synthetic import SyntheticDAQ
        
        SyntheticDAQ(self.dummy_model.configuration)

    def test_synthetic_camera(self):
        from aslm.model.devices.camera.camera_synthetic import SyntheticCamera, SyntheticCameraController

        scc = SyntheticCameraController()
        SyntheticCamera(self.microscope_name, scc, self.dummy_model.configuration)

    def test_synthetic_stage(self):
        from aslm.model.devices.stages.stage_synthetic import SyntheticStage

        SyntheticStage(self.microscope_name, None, self.dummy_model.configuration)

    def test_synthetic_zoom(self):
        from aslm.model.devices.zoom.zoom_synthetic import SyntheticZoom

        SyntheticZoom(self.microscope_name, None, self.dummy_model.configuration)

    def test_synthetic_shutter(self):
        from aslm.model.devices.shutter.laser_shutter_synthetic import SyntheticShutter

        SyntheticShutter(self.microscope_name, None, self.dummy_model.configuration)

    def test_synthetic_laser(self):
        from aslm.model.devices.lasers.laser_synthetic import SyntheticLaser

        SyntheticLaser(self.microscope_name, None, self.dummy_model.configuration, 0)
