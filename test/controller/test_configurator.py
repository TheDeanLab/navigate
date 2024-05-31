import unittest
from unittest.mock import MagicMock, patch, mock_open
from navigate.controller.configurator import Configurator, write_to_yaml
import tkinter as tk


class DummySplashScreen:
    def destroy(self):
        pass


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


class TestConfigurator(unittest.TestCase):
    def setUp(self):
        root = tk.Tk()
        self.configurator = Configurator(root, DummySplashScreen())

    def test_add_microscope(self):
        microscopes = self.configurator.microscope_id
        self.configurator.add_microscope()
        assert self.configurator.microscope_id == microscopes + 1

    def test_delete_microscopes(self):
        self.configurator.add_microscope()
        self.configurator.delete_microscopes()
        assert self.configurator.microscope_id == 0

    def test_new_configuration(self):
        self.configurator.new_configuration()
        assert self.configurator.microscope_id == 0

    @patch("navigate.controller.configurator.write_to_yaml")
    @patch("tkinter.filedialog.asksaveasfilename")
    def test_save_return(self, mock_asksaveasfilename, mock_write_to_yaml):
        # Mock write_to_yaml to see if it gets called.
        self.configurator.write_to_yaml = MagicMock()

        # Mocking filedialog to return a test filename
        mock_asksaveasfilename.return_value = ""
        self.configurator.save()
        mock_write_to_yaml.assert_not_called()

    def test_create_config_window(self):
        pass

    def test_load_configuration(self):
        pass

    def test_device_selected(self):
        pass
