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
import unittest

# Third Party Imports
import pytest

# Local Imports
from aslm.controller.sub_controllers.menu_controller import MenuController, FakeEvent


class TestFakeEvent(unittest.TestCase):
    def test_fake_event_creation(self):
        fake_event = FakeEvent(char="a", keysym="A")
        self.assertEqual(fake_event.char, "a")
        self.assertEqual(fake_event.keysym, "A")
        self.assertEqual(fake_event.state, 0)


class TestMenuController(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        c = dummy_controller
        v = dummy_controller.view
        self.menu_controller = MenuController(v, c)

    def test_attributes(self):
        methods = dir(MenuController)
        desired_methods = [
            "initialize_menus",
            "populate_menu",
            "new_experiment",
            "load_experiment",
            "save_experiment",
            "load_images",
            "popup_camera_map_setting",
            "popup_ilastik_setting",
            "popup_help",
            "toggle_stage_limits",
            "popup_autofocus_setting",
            "popup_waveform_setting",
            "popup_microscope_setting",
            "toggle_save",
            "acquire_data",
            "not_implemented",
            "stage_movement",
            "switch_tabs",
        ]

        for method in desired_methods:
            assert method in methods

    def test_popup_camera_map_setting(self):
        assert (
            hasattr(
                self.menu_controller.parent_controller, "camera_map_popup_controller"
            )
            is False
        )
        self.menu_controller.popup_camera_map_setting()
        assert (
            hasattr(
                self.menu_controller.parent_controller, "camera_map_popup_controller"
            )
            is True
        )

    def test_popup_help(self):
        assert (
            hasattr(self.menu_controller.parent_controller, "help_controller") is False
        )
        self.menu_controller.popup_help()
        assert (
            hasattr(self.menu_controller.parent_controller, "help_controller") is True
        )

    def test_autofocus_settings(self):
        assert (
            hasattr(self.menu_controller.parent_controller, "af_popup_controller")
            is False
        )
        self.menu_controller.popup_autofocus_setting()
        assert (
            hasattr(self.menu_controller.parent_controller, "af_popup_controller")
            is True
        )

    def test_popup_waveform_setting(self):
        # TODO: Incomplete.
        assert (
            hasattr(self.menu_controller.parent_controller, "waveform_popup_controller")
            is False
        )

    def test_popup_microscope_setting(self):
        # TODO: Incomplete. DummyController has no attribute 'model'
        assert (
            hasattr(
                self.menu_controller.parent_controller, "microscope_popup_controller"
            )
            is False
        )

    def test_toggle_save(self):
        self.menu_controller.save_data = False
        self.menu_controller.toggle_save()
        assert self.menu_controller.save_data is True
        self.menu_controller.toggle_save()
        assert self.menu_controller.save_data is False

    def test_stage_movement(self):
        # TODO: DummyController does not have a stage controller.
        pass

    def test_switch_tabs(self):
        for i in range(1, 4):
            self.menu_controller.switch_tabs(i)
            assert (
                self.menu_controller.parent_controller.view.settings.index("current")
                == i - 1
            )
