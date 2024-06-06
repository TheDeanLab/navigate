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
from unittest.mock import MagicMock, patch
import tkinter as tk

# Third Party Imports
import pytest

# Local Imports
from navigate.controller.sub_controllers.menu_controller import (
    MenuController,
    FakeEvent,
)


class TestFakeEvent(unittest.TestCase):
    def test_fake_event_creation(self):
        fake_event = FakeEvent(char="a", keysym="A")
        self.assertEqual(fake_event.char, "a")
        self.assertEqual(fake_event.keysym, "A")
        self.assertEqual(fake_event.state, 0)


class TestStageMovement(unittest.TestCase):
    def setUp(self):
        # Create a mock parent controller and view
        self.root = tk.Tk()
        self.parent_controller = MagicMock()
        self.parent_controller.stage_controller = MagicMock()
        self.view = MagicMock()
        self.view.root = self.root

        # Initialize the menu controller
        self.mc = MenuController(self.view, self.parent_controller)

    def tearDown(self):
        self.root.destroy()

    def test_initialize_menus(self):
        self.mc.initialize_menus()

    def test_stage_movement_with_ttk_entry(self):
        self.mc.parent_controller.view.focus_get.return_value = MagicMock(
            widgetName="ttk::entry"
        )
        self.mc.stage_movement("a")
        self.mc.parent_controller.stage_controller.stage_key_press.assert_not_called()

    def test_stage_movement_with_ttk_combobox(self):
        self.mc.parent_controller.view.focus_get.return_value = MagicMock(
            widgetName="ttk::combobox"
        )
        self.mc.stage_movement("a")
        self.mc.parent_controller.stage_controller.stage_key_press.assert_not_called()

    def test_stage_movement_with_other_widget(self):
        self.mc.parent_controller.view.focus_get.return_value = MagicMock(
            widgetName="other_widget"
        )
        self.mc.stage_movement("a")
        self.mc.parent_controller.stage_controller.stage_key_press.assert_called_with(
            self.mc.fake_event
        )

    def test_stage_movement_with_key_error(self):
        self.mc.parent_controller.view.focus_get.side_effect = KeyError
        # Test that no exception is raised
        try:
            self.mc.stage_movement("a")
        except KeyError:
            self.fail("stage_movement() raised KeyError unexpectedly!")

    def test_stage_movement_with_no_focus(self):
        self.mc.parent_controller.view.focus_get.return_value = None
        self.mc.stage_movement("a")
        self.mc.parent_controller.stage_controller.stage_key_press.assert_called_with(
            self.mc.fake_event
        )


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
        class MockWidget:
            def __int__(self):
                self.value = False

            def set(self, value):
                self.value = value

            def get(self):
                return self.value

        channel_tab_controller = MagicMock()
        self.menu_controller.parent_controller.channels_tab_controller = (
            channel_tab_controller
        )
        channel_tab_controller.timepoint_vals = {"is_save": MockWidget()}
        temp = self.menu_controller.view.settings.channels_tab.stack_timepoint_frame
        temp.save_data.get = MagicMock(return_value=False)
        self.menu_controller.toggle_save()
        assert channel_tab_controller.timepoint_vals["is_save"].get() is True

        temp = self.menu_controller.view.settings.channels_tab.stack_timepoint_frame
        temp.save_data.get = MagicMock(return_value=True)
        self.menu_controller.toggle_save()
        assert channel_tab_controller.timepoint_vals["is_save"].get() is False

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

    @patch("src.navigate.controller.sub_controllers.menu_controller.platform.system")
    @patch(
        "src.navigate.controller.sub_controllers.menu_controller.subprocess.check_call"
    )
    def test_open_folder(self, mock_check_call, mock_system):
        mock_system.return_value = "Darwin"
        self.menu_controller.open_folder("test_path")
        mock_check_call.assert_called_once_with(["open", "--", "test_path"])

        mock_check_call.reset_mock()
        mock_system.return_value = "Windows"
        self.menu_controller.open_folder("test_path")
        mock_check_call.assert_called_once_with(["explorer", "test_path"])

        mock_check_call.reset_mock()
        mock_system.return_value = "Linux"
        self.menu_controller.open_folder("test_path")
        self.assertEqual(mock_check_call.call_count, 0)

    @patch("src.navigate.controller.sub_controllers.menu_controller.os.path.join")
    def test_open_log_files(self, mock_join):
        with patch.object(self.menu_controller, "open_folder") as mock_open_folder:
            mock_join.return_value = "joined_path"
            self.menu_controller.open_log_files()
            mock_open_folder.assert_called_once_with("joined_path")

    @patch("src.navigate.controller.sub_controllers.menu_controller.os.path.join")
    def test_open_configuration_files(self, mock_join):
        with patch.object(self.menu_controller, "open_folder") as mock_open_folder:
            mock_join.return_value = "joined_path"
            self.menu_controller.open_configuration_files()
            mock_open_folder.assert_called_once_with("joined_path")
