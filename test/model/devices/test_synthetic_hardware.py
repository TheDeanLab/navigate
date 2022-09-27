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

# Third Party Imports

# Local Imports
from aslm.model.dummy import DummyModel


class TestSyntheticHardware():

    def test_synthetic_daq(self):
        from aslm.model.devices.daq.daq_synthetic import SyntheticDAQ
        self.dummy_model = DummyModel()
        self.config = self.dummy_model.configuration
        sd = SyntheticDAQ(configuration=self.config)

        assert True



    def test_synthetic_camera(self):
        from aslm.model.devices.camera.camera_synthetic import SyntheticCamera
        self.dummy_model = DummyModel()
        self.config = self.dummy_model.configuration
        sc = SyntheticCamera(configuration=self.config, camera_id=0)

        return True

    def test_synthetic_stage(self):
        from aslm.model.devices.stages.stage_synthetic import SyntheticStage
        self.dummy_model = DummyModel()
        self.config = self.dummy_model.configuration



        ss = SyntheticStage(configuration=self.config)

    def test_synthetic_zoom(self):
        from aslm.model.devices.zoom.zoom_synthetic import SyntheticZoom
        self.dummy_model = DummyModel()
        self.config = self.dummy_model.configuration


        sz = SyntheticZoom(configuration=self.config)

        return True

    def test_synthetic_shutter(self):
        from aslm.model.devices.shutter.laser_shutter_synthetic import SyntheticShutter
        self.dummy_model = DummyModel()
        self.config = self.dummy_model.configuration



        ss = SyntheticShutter(configuration=self.config)

        return True

    # def test_synthetic_laser(self):
    #     from aslm.model.devices.laser_trigger_synthetic import SyntheticLaserTriggers
    #     from aslm.model.devices.lasers.SyntheticLaser import SyntheticLaser
    #     self.dummy_model = DummyModel()
    #     self.config = self.dummy_model.configuration
    #     self.experiment = self.dummy_model.experiment
    #     self.etl_const = self.dummy_model.etl_constants
    #
    #     sl = SyntheticLaser(self.config, False)
    #
    #     return True
