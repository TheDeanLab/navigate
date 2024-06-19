import unittest
from unittest.mock import patch, mock_open
from navigate.controller.configurator import Configurator, write_to_yaml
import tkinter as tk
import pytest
from pathlib import Path


class DummySplashScreen:
    def destroy(self):
        pass


def get_config_path():
    current_path = Path(__file__).resolve()
    project_root = current_path.parents[2]
    config_path = Path(project_root, "src", "navigate", "config", "configuration.yaml")
    return config_path


class TestWriteToYaml(unittest.TestCase):
    def test_write_to_yaml(self):
        # Sample configuration dictionary
        config = {
            "Microscope 1": {
                "Hardware 1": {
                    "var1": "value1",
                    "var2": "value2",
                },
                "Hardware 2": {
                    "var3": "value3",
                    "var4": "value4",
                },
            }
        }

        # Expected YAML content
        expected_content = (
            "microscopes:\n"
            "  Microscope 1:\n"
            "    Hardware 1:\n"
            "      var1: value1\n"
            "      var2: value2\n"
            "    Hardware 2:\n"
            "      var3: value3\n"
            "      var4: value4\n"
        )

        # Use mock_open to mock the open function
        mock_file = mock_open()

        with patch("builtins.open", mock_file):
            write_to_yaml(config, "test_config.yml")

        # Retrieve the actual written content from the mock
        mock_file().write.assert_called()  # Ensure write was called
        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )

        # Assert that the actual written content matches the expected content
        self.assertEqual(written_content, expected_content)


@pytest.fixture(scope="session")
def configurator():
    root = tk.Tk()
    configurator = Configurator(root, DummySplashScreen())
    return configurator


def test_add_microscope(configurator):
    microscopes = configurator.microscope_id
    configurator.add_microscope()
    assert configurator.microscope_id == microscopes + 1


def test_delete_microscopes(configurator):
    configurator.add_microscope()
    configurator.delete_microscopes()
    assert configurator.microscope_id == 0


def test_new_configuration(configurator):
    configurator.new_configuration()
    assert configurator.microscope_id == 0


def test_save_return(configurator):
    with patch("tkinter.filedialog.asksaveasfilename") as asksaveasfilename:
        with patch("navigate.controller.configurator.write_to_yaml") as write_to_yaml:
            # Mocking filedialog to return a test filename
            asksaveasfilename.return_value = ""
            configurator.save()
            write_to_yaml.assert_not_called()


def test_save(configurator):
    with patch("tkinter.filedialog.asksaveasfilename") as asksaveasfilename:
        asksaveasfilename.return_value = get_config_path().with_name("test_config.yaml")

        with patch("tkinter.filedialog.askopenfilename") as askopenfilename:
            askopenfilename.return_value = get_config_path()
            configurator.load_configuration()

            with patch("tkinter.messagebox.showwarning"):
                mock_file = mock_open()

                with patch("builtins.open", mock_file):
                    configurator.save()
                    mock_file().write.assert_called()


def test_create_config_window(configurator):
    configurator.create_config_window(1)


def test_load_configuration_return(configurator):
    with patch("tkinter.filedialog.askopenfilename") as askopenfilename:
        with patch("navigate.tools.file_functions.load_yaml_file") as load_yaml_file:
            askopenfilename.return_value = ""
            configurator.load_configuration()
            load_yaml_file.assert_not_called()


def test_load_configuration_error(configurator):
    with patch("tkinter.filedialog.askopenfilename") as askopenfilename:
        with patch("navigate.tools.file_functions.load_yaml_file") as load_yaml_file:
            with patch("tkinter.messagebox.showerror") as showerror:
                askopenfilename.return_value = "alphabet.yaml"
                load_yaml_file.return_value = {"incorrect_dict": 5}
                configurator.load_configuration()
                showerror.assert_called()


def test_load_configuration(configurator):
    with patch("tkinter.filedialog.askopenfilename") as askopenfilename:
        askopenfilename.return_value = get_config_path()
        configurator.load_configuration()
        tab_list = configurator.view.microscope_window.tab_list
        expected_microscopes = ["Nanoscale", "Mesoscale"]
        for microscope in expected_microscopes:
            assert microscope in tab_list


def test_device_selected(self):
    pass
