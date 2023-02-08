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
import pytest


class TestChannelSettingController:
    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        from aslm.controller.sub_controllers.channels_tab_controller import (
            ChannelsTabController,
        )
        from aslm.controller.sub_controllers.channel_setting_controller import (
            ChannelSettingController,
        )

        self.ctc = ChannelsTabController(
            dummy_controller.view.settings.channels_tab, dummy_controller
        )
        self.ctc.commands = []
        self.ctc.execute = lambda command: self.ctc.commands.append(command)

        self.channel_setting = ChannelSettingController(
            self.ctc.view.channel_widgets_frame,
            self.ctc,
            dummy_controller.configuration_controller,
        )

    @pytest.mark.parametrize(
        "mode,state,state_readonly",
        [("stop", "normal", "readonly"), ("live", "disabled", "disabled")],
    )
    def test_set_mode(self, mode, state, state_readonly):

        self.channel_setting.set_mode(mode)

        for i in range(5):
            assert str(self.channel_setting.view.channel_checks[i]["state"]) == state
            assert str(self.channel_setting.view.interval_spins[i]["state"]) == state
            assert (
                str(self.channel_setting.view.laser_pulldowns[i]["state"])
                == state_readonly
            )
            if self.channel_setting.mode != "live" or (
                self.channel_setting.mode == "live"
                and not self.channel_setting.view.channel_variables[i].get()
            ):
                assert (
                    str(self.channel_setting.view.exptime_pulldowns[i]["state"])
                    == state
                )
            if not self.channel_setting.view.channel_variables[i].get():
                assert (
                    str(self.channel_setting.view.laserpower_pulldowns[i]["state"])
                    == state
                )
                assert (
                    str(self.channel_setting.view.filterwheel_pulldowns[i]["state"])
                    == state
                )
                assert str(self.channel_setting.view.defocus_spins[i]["state"]) == state

    def test_channel_callback(self):
        import random

        self.channel_setting.in_initialization = False
        channel_dict = (
            self.channel_setting.parent_controller.parent_controller.configuration[
                "experiment"
            ]["MicroscopeState"]["channels"]
        )
        # shuffle the channels
        new_channel_dict = {
            k: v
            for k, v in zip(
                channel_dict.keys(),
                random.choices(channel_dict.values(), k=len(channel_dict.keys())),
            )
        }

        self.channel_setting.populate_experiment_values(channel_dict)
        for channel_id in range(self.channel_setting.num):
            vals = self.channel_setting.get_vals_by_channel(channel_id)
            channel_key = f"channel_{str(channel_id + 1)}"
            try:
                setting_dict = channel_dict[channel_key]
                new_setting_dict = new_channel_dict[channel_key]
            except KeyError:
                continue

            # Test channel callback through trace writes
            for k in setting_dict.keys():
                if k == "laser_index" or k == "filter_position":
                    continue
                if k == "defocus":
                    new_val = float(random.randint(1, 10))
                else:
                    new_val = new_setting_dict[k]

                vals[k].set(new_val)

                assert str(vals[k].get()) == str(new_val)
                if k != "defocus":
                    assert setting_dict[k] == new_setting_dict[k]

                if k == "laser":
                    assert (
                        setting_dict["laser_index"] == new_setting_dict["laser_index"]
                    )
                elif k == "filter":
                    assert (
                        setting_dict["filter_position"]
                        == new_setting_dict["filter_position"]
                    )
                elif k == "camera_exposure_time" or k == "is_selected":
                    assert (
                        self.channel_setting.parent_controller.commands.pop()
                        == "recalculate_timepoint"
                    )
                    self.channel_setting.parent_controller.commands = []  # reset

    def test_get_vals_by_channel(self):
        # Not needed to test IMO
        pass

    def test_get_index(self):
        # Not needed to test IMO
        pass
