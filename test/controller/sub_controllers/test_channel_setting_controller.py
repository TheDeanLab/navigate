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


from aslm.controller.sub_controllers.channel_setting_controller import ChannelSettingController
from unittest.mock import MagicMock
import pytest

class TestChannelSettingController():
    
    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        c = dummy_controller
        self.v = dummy_controller.view
        
        self.channel_setting = ChannelSettingController(self.v.settings.channels_tab.channel_widgets_frame, c, c.configuration_controller)


    @pytest.mark.parametrize('mode,state,state_readonly', [("stop", "normal", "readonly"), ("live", "disabled", "disabled")])
    def test_set_mode(self, mode, state, state_readonly):


        self.channel_setting.set_mode(mode)

        for i in range(5):
            assert str(self.channel_setting.view.channel_checks[i]['state']) == state
            assert str(self.channel_setting.view.interval_spins[i]['state']) == state
            assert str(self.channel_setting.view.laser_pulldowns[i]['state']) == state_readonly
            if self.channel_setting.mode != "live" or (
                self.channel_setting.mode == "live" and not self.channel_setting.view.channel_variables[i].get()
            ):
                assert str(self.channel_setting.view.exptime_pulldowns[i]['state']) == state
            if not self.channel_setting.view.channel_variables[i].get():
                assert str(self.channel_setting.view.laserpower_pulldowns[i]['state']) == state
                assert str(self.channel_setting.view.filterwheel_pulldowns[i]["state"]) == state
                assert str(self.channel_setting.view.defocus_spins[i]['state']) == state


    def test_channel_callback(self):
        # Over my head to test
        pass


    def test_get_vals_by_channel(self):
        # Not needed to test IMO
        pass


    def test_get_index(self):
        # Not needed to test IMO
        pass