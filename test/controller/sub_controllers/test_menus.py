# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
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

# Third Party Imports
import pytest

# Local Imports
from navigate.controller.sub_controllers.menus import (
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
        # Patch tkinter variables so tests do not require a real Tcl/Tk runtime.
        self.stringvar_patcher = patch(
            "navigate.controller.sub_controllers.menus.tk.StringVar",
            return_value=MagicMock(),
        )
        self.intvar_patcher = patch(
            "navigate.controller.sub_controllers.menus.tk.IntVar",
            return_value=MagicMock(),
        )
        self.booleanvar_patcher = patch(
            "navigate.controller.sub_controllers.menus.tk.BooleanVar",
            return_value=MagicMock(),
        )
        self.stringvar_patcher.start()
        self.intvar_patcher.start()
        self.booleanvar_patcher.start()

        # Create a mock parent controller and view
        self.parent_controller = MagicMock()
        self.parent_controller.stage_controller = MagicMock()
        self.view = MagicMock()
        self.view.root = MagicMock()
        self.parent_controller.view = self.view

        # Initialize the menu controller
        self.mc = MenuController(self.view, self.parent_controller)

        # Mock the histogram configuration entry.
        self.parent_controller.configuration["gui"]["histogram"] = MagicMock()
        self.parent_controller.configuration["gui"]["histogram"].get.return_value = True

    def tearDown(self):
        self.booleanvar_patcher.stop()
        self.intvar_patcher.stop()
        self.stringvar_patcher.stop()

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

    def test_initialize_menus_wires_multiposition_stage_commands(self):
        multiposition_controller = (
            self.menu_controller.parent_controller.multiposition_tab_controller
        )
        multiposition_controller.load_positions = MagicMock()
        multiposition_controller.export_positions = MagicMock()
        multiposition_controller.add_stage_position = MagicMock()
        self.menu_controller.parent_controller.configuration["gui"]["histogram"] = {
            "enabled": True
        }

        self.menu_controller.initialize_menus()
        stage_menu = self.menu_controller.view.menubar.menu_multi_positions

        def invoke_latest_entry(label):
            end_idx = int(stage_menu.index("end"))
            matches = []
            for idx in range(end_idx + 1):
                try:
                    if stage_menu.entrycget(idx, "label") == label:
                        matches.append(idx)
                except Exception:
                    continue
            assert matches, f"Missing stage menu entry: {label}"
            stage_menu.invoke(matches[-1])

        invoke_latest_entry("Load Positions")
        invoke_latest_entry("Export Positions")
        invoke_latest_entry("Append Current Position")

        multiposition_controller.load_positions.assert_called_once()
        multiposition_controller.export_positions.assert_called_once()
        multiposition_controller.add_stage_position.assert_called_once()

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
            self.menu_controller.switch_tabs(window="left", tab=i)
            assert (
                self.menu_controller.parent_controller.view.settings.index("current")
                == i - 1
            )

    @patch("src.navigate.controller.sub_controllers.menus.platform.system")
    @patch("src.navigate.controller.sub_controllers.menus.subprocess.check_call")
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

    @patch("src.navigate.controller.sub_controllers.menus.os.path.join")
    def test_open_log_files(self, mock_join):
        with patch.object(self.menu_controller, "open_folder") as mock_open_folder:
            mock_join.return_value = "joined_path"
            self.menu_controller.open_log_files()
            mock_open_folder.assert_called_once_with("joined_path")

    @patch("src.navigate.controller.sub_controllers.menus.os.path.join")
    def test_open_configuration_files(self, mock_join):
        with patch.object(self.menu_controller, "open_folder") as mock_open_folder:
            mock_join.return_value = "joined_path"
            self.menu_controller.open_configuration_files()
            mock_open_folder.assert_called_once_with("joined_path")


@pytest.fixture
def menu_controller_for_branches(dummy_controller):
    return MenuController(dummy_controller.view, dummy_controller)


@patch("navigate.controller.sub_controllers.menus.filedialog.askopenfilename")
def test_load_experiment_branches(mock_askopenfilename, menu_controller_for_branches):
    controller = menu_controller_for_branches
    controller.parent_controller.populate_experiment_setting = MagicMock()

    mock_askopenfilename.return_value = ""
    controller.load_experiment()
    controller.parent_controller.populate_experiment_setting.assert_not_called()

    mock_askopenfilename.return_value = "/tmp/experiment.yml"
    controller.load_experiment()
    controller.parent_controller.populate_experiment_setting.assert_called_once_with(
        "/tmp/experiment.yml"
    )


@patch("navigate.controller.sub_controllers.menus.save_yaml_file")
@patch("navigate.controller.sub_controllers.menus.filedialog.asksaveasfilename")
@patch("navigate.controller.sub_controllers.menus.messagebox.showerror")
def test_save_experiment_branches(
    mock_showerror, mock_asksave, mock_save_yaml, menu_controller_for_branches
):
    controller = menu_controller_for_branches

    controller.parent_controller.update_experiment_setting = MagicMock(return_value="bad")
    controller.save_experiment()
    mock_showerror.assert_called_once()
    mock_save_yaml.assert_not_called()

    mock_showerror.reset_mock()
    controller.parent_controller.update_experiment_setting = MagicMock(return_value=None)
    mock_asksave.return_value = ""
    controller.save_experiment()
    mock_showerror.assert_not_called()
    mock_save_yaml.assert_not_called()

    mock_asksave.return_value = "/tmp/experiment.yml"
    controller.save_experiment()
    mock_save_yaml.assert_called_once()


@patch("navigate.controller.sub_controllers.menus.save_yaml_file")
@patch("navigate.controller.sub_controllers.menus.filedialog.asksaveasfilename")
def test_save_waveform_constants_branches(
    mock_asksave, mock_save_yaml, menu_controller_for_branches
):
    controller = menu_controller_for_branches
    mock_asksave.return_value = ""
    controller.save_waveform_constants()
    mock_save_yaml.assert_not_called()

    mock_asksave.return_value = "/tmp/waveforms.yml"
    controller.save_waveform_constants()
    mock_save_yaml.assert_called_once()


@patch("navigate.controller.sub_controllers.menus.verify_waveform_constants")
@patch("navigate.controller.sub_controllers.menus.update_config_dict")
@patch("navigate.controller.sub_controllers.menus.filedialog.askopenfilename")
def test_load_waveform_constants_branches(
    mock_askopenfilename,
    mock_update_config,
    mock_verify_waveforms,
    menu_controller_for_branches,
):
    controller = menu_controller_for_branches
    mock_askopenfilename.return_value = ""

    controller.load_waveform_constants()
    mock_update_config.assert_not_called()

    controller.parent_controller.waveform_popup_controller = MagicMock()
    mock_askopenfilename.return_value = "/tmp/waveforms.yml"
    controller.load_waveform_constants()

    mock_update_config.assert_called_once()
    mock_verify_waveforms.assert_called_once()
    controller.parent_controller.waveform_popup_controller.populate_experiment_values.assert_called_once_with(
        force_update=True
    )


@patch("navigate.controller.sub_controllers.menus.filedialog.askopenfilenames")
def test_load_images_branches(mock_askopenfilenames, menu_controller_for_branches):
    controller = menu_controller_for_branches
    controller.parent_controller.model = MagicMock()
    controller.parent_controller.model.load_images = MagicMock()

    mock_askopenfilenames.return_value = ()
    controller.load_images()
    controller.parent_controller.model.load_images.assert_not_called()

    mock_askopenfilenames.return_value = ("/tmp/a.tif", "/tmp/b.tif")
    controller.load_images()
    controller.parent_controller.model.load_images.assert_called_once_with(
        ("/tmp/a.tif", "/tmp/b.tif")
    )


def test_toggle_stage_limits_branches(menu_controller_for_branches):
    controller = menu_controller_for_branches
    controller.parent_controller.execute = MagicMock()
    controller.parent_controller.stage_limits_popup_controller = MagicMock()
    controller.disable_stage_limits = MagicMock()

    controller.disable_stage_limits.get.return_value = 1
    controller.toggle_stage_limits()
    assert (
        controller.parent_controller.configuration["experiment"]["StageParameters"][
            "limits"
        ]
        is False
    )
    controller.parent_controller.execute.assert_called_with("stage_limits", False)
    controller.parent_controller.stage_limits_popup_controller.view.enable_stage_limits_var.set.assert_called_with(
        False
    )

    controller.disable_stage_limits.get.return_value = 0
    controller.toggle_stage_limits()
    assert (
        controller.parent_controller.configuration["experiment"]["StageParameters"][
            "limits"
        ]
        is True
    )
    controller.parent_controller.execute.assert_called_with("stage_limits", True)


@patch("navigate.controller.sub_controllers.menus.WaveformPopupController")
@patch("navigate.controller.sub_controllers.menus.WaveformParameterPopupWindow")
def test_popup_waveform_setting_branches(
    mock_waveform_popup_window,
    mock_waveform_popup_controller,
    menu_controller_for_branches,
):
    controller = menu_controller_for_branches

    controller.parent_controller.waveform_popup_controller = MagicMock()
    controller.popup_waveform_setting()
    controller.parent_controller.waveform_popup_controller.showup.assert_called_once()

    delattr(controller.parent_controller, "waveform_popup_controller")
    created_controller = MagicMock()
    mock_waveform_popup_controller.return_value = created_controller
    controller.popup_waveform_setting()

    mock_waveform_popup_window.assert_called_once()
    created_controller.populate_experiment_values.assert_called_once()
    assert controller.parent_controller.waveform_popup_controller is created_controller


@patch("navigate.controller.sub_controllers.menus.MicroscopePopupController")
def test_popup_microscope_setting_branches(
    mock_microscope_popup_controller, menu_controller_for_branches
):
    controller = menu_controller_for_branches
    controller.parent_controller.model = MagicMock()

    controller.parent_controller.microscope_popup_controller = MagicMock()
    controller.popup_microscope_setting()
    controller.parent_controller.microscope_popup_controller.showup.assert_called_once()

    delattr(controller.parent_controller, "microscope_popup_controller")
    controller.parent_controller.model.get_microscope_info = MagicMock(
        return_value={"info": "value"}
    )
    created_controller = MagicMock()
    mock_microscope_popup_controller.return_value = created_controller

    controller.popup_microscope_setting()

    controller.parent_controller.model.get_microscope_info.assert_called_once()
    assert controller.parent_controller.microscope_popup_controller is created_controller
