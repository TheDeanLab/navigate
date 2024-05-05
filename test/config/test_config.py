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
#

# Standard Imports
import pathlib
import unittest
from unittest.mock import patch, MagicMock
from multiprocessing import Manager
from multiprocessing.managers import ListProxy, DictProxy
import os
import time
import random
import yaml
import sys

# Third Party Imports

# Local Imports
import navigate.config.config as config
from navigate.tools.file_functions import save_yaml_file, delete_folder, load_yaml_file


def test_config_methods():
    methods = dir(config)
    desired_methods = [
        "DictProxy",
        "ListProxy",
        "Path",
        "__builtins__",
        "__cached__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__spec__",
        "build_nested_dict",
        "get_navigate_path",
        "get_configuration_paths",
        "isfile",
        "load_configs",
        "os",
        "platform",
        "shutil",
        "sys",
        "time",
        "update_config_dict",
        "verify_experiment_config",
        "verify_waveform_constants",
        "verify_configuration",
        "yaml",
        "build_ref_name"
    ]
    for method in methods:
        assert method in desired_methods


def test_get_navigate_path():
    """Test that the Navigate path is a string."""
    assert isinstance(config.get_navigate_path(), str)
    path_string = config.get_navigate_path()
    assert ".navigate" in path_string


def test_get_navigate_path_windows(monkeypatch):
    """Test that the Navigate path is a string."""
    monkeypatch.setattr(config.platform, "system", lambda: "Windows")
    monkeypatch.setattr(config.os, "getenv", lambda x: "LOCALAPPDATA")
    monkeypatch.setattr(config.os.path, "exists", lambda x: True)
    assert isinstance(config.get_navigate_path(), str)
    path_string = config.get_navigate_path()
    assert path_string.startswith("LOCALAPPDATA")
    assert path_string.endswith(".navigate")

    


def test_get_navigate_path_mac(monkeypatch):
    """Test that the Navigate path is a string."""
    monkeypatch.setattr(config.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(config.os, "getenv", lambda x: "HOME")
    monkeypatch.setattr(config.os.path, "exists", lambda x: True)
    assert isinstance(config.get_navigate_path(), str)
    path_string = config.get_navigate_path()
    assert path_string.startswith("HOME")
    assert path_string.endswith(".navigate")


# Write a test for config.get_configuration_paths()
def test_get_configuration_paths():
    """Test that the configuration paths are a list."""
    paths = config.get_configuration_paths()
    for path in paths:
        assert isinstance(path, pathlib.Path)
    assert len(paths) == 5


def test_get_configuration_paths_create_dir(monkeypatch):
    """Test that the configuration path is created,
    and that they are a list."""
    monkeypatch.setattr(config, "get_navigate_path", lambda: "TESTPATH")
    paths = config.get_configuration_paths()
    for path in paths:
        assert isinstance(path, pathlib.Path)
        assert os.path.exists(path), "Each configuration yaml file is copied"
        assert path.suffix.lower() in [".yml", ".yaml"]
    # delete generated folder
    delete_folder("TESTPATH")

# test that the system is exited if no file is provided to load_yaml_config
def test_load_yaml_config_no_file():
    """Test that the system exits if no file is provided."""
    from unittest import mock

    with mock.patch("sys.exit") as mock_sys_exit:
        config.load_configs(manager=Manager(), **{})
        mock_sys_exit.assert_called_once()


class TestLoadConfigsWithYAMLError(unittest.TestCase):
    """Test the load_configs function.

    Target is the yaml.YAMLError exception clause.
    """

    @patch("yaml.load")
    @patch("builtins.open")
    @patch("pathlib.Path.exists")
    def test_yaml_error(self, mock_exists, mock_open, mock_yaml_load):
        # Set up the mocks
        mock_exists.return_value = True
        mock_open.return_value = MagicMock()
        mock_yaml_load.side_effect = yaml.YAMLError("Test YAMLError")

        # Mocking sys.exit to prevent the test runner from exiting
        with patch.object(sys, "exit") as mock_exit:
            manager = MagicMock()
            config.load_configs(manager, config1="path/to/config1.yaml")

            # Check if sys.exit was called with the expected argument
            mock_exit.assert_called_with(1)

            # Check if the YAMLError was triggered
            mock_yaml_load.assert_called_once()


class TestBuildNestedDict(unittest.TestCase):
    def setUp(self):
        self.manager = Manager()
        self.parent_dict = {}
        self.key_name = "nested_dict"

    def tearDown(self):
        self.manager.shutdown()

    def test_build_nested_dict_with_string_data(self):
        string_data = "string"
        expected_result = {"nested_dict": "string"}

        config.build_nested_dict(
            self.manager, self.parent_dict, self.key_name, string_data
        )

        self.assertEqual(self.parent_dict, expected_result)
        self.assertEqual(self.parent_dict[self.key_name], "string")
        assert isinstance(self.parent_dict, dict)

    def test_build_nested_dict_with_list_data(self):
        list_data = ["string1", "string2"]

        config.build_nested_dict(
            self.manager, self.parent_dict, self.key_name, list_data
        )

        assert isinstance(self.parent_dict, dict)
        assert isinstance(self.parent_dict[self.key_name], ListProxy)
        for i in range(2):
            assert self.parent_dict[self.key_name][i] == list_data[i]

    def test_build_nested_dict_with_dict_data(self):
        dict_data = {"key1": "string1", "key2": "string2"}

        config.build_nested_dict(
            self.manager, self.parent_dict, self.key_name, dict_data
        )

        assert isinstance(self.parent_dict, dict)
        assert isinstance(self.parent_dict[self.key_name], DictProxy)
        for key in dict_data.keys():
            assert self.parent_dict[self.key_name][key] == dict_data[key]

    def test_update_config_dict_with_bad_file_name(self):
        test_entry = "string"
        dict_data = {"key1": "string1", "key2": "string2"}
        # Build the nested config
        config.build_nested_dict(
            self.manager, self.parent_dict, self.key_name, dict_data
        )

        # Update the nested config
        result = config.update_config_dict(
            self.manager, self.parent_dict, self.key_name, test_entry
        )
        assert result is False

    def test_update_config_dict_with_file_name(self):
        test_entry = "test.yml"
        # create an yaml file
        test_yaml_data = {"test_key1": "test_string1", "test_key2": "test_string2"}
        save_yaml_file("", test_yaml_data, test_entry)

        dict_data = {"key1": "string1", "key2": "string2"}
        # Build the nested config
        config.build_nested_dict(
            self.manager, self.parent_dict, self.key_name, dict_data
        )

        # Update the nested config
        result = config.update_config_dict(
            self.manager, self.parent_dict, self.key_name, test_entry
        )

        assert result is True
        assert isinstance(self.parent_dict[self.key_name], DictProxy)
        for k in self.parent_dict[self.key_name].keys():
            assert self.parent_dict[self.key_name][k] == test_yaml_data[k]

        # delete test yaml file
        os.remove(test_entry)


class TestVerifyExperimentConfig(unittest.TestCase):
    def setUp(self):
        self.manager = Manager()
        current_path = os.path.abspath(os.path.dirname(__file__))
        root_path = os.path.dirname(os.path.dirname(current_path))
        self.config_path = os.path.join(root_path, "src", "navigate", "config")
        self.test_root = "test_dir"
        os.mkdir(self.test_root)

        configuration = config.load_configs(
            self.manager,
            configuration=os.path.join(self.config_path, "configuration.yaml"),
        )
        saving_dict_sample = {
            "root_directory": config.get_navigate_path(),
            "save_directory": config.get_navigate_path(),
            "user": "Kevin",
            "tissue": "Lung",
            "celltype": "MV3",
            "label": "GFP",
            "file_type": "TIFF",
            "date": time.strftime("%Y-%m-%d"),
            "solvent": "BABB",
        }

        camera_parameters_dict_sample = {
            "x_pixels": 2048,
            "y_pixels": 2048,
            "img_x_pixels": 2048,
            "img_y_pixels": 2048,
            "sensor_mode": "Normal",
            "readout_direction": "Top-to-Bottom",
            "number_of_pixels": 10,
            "binning": "1x1",
            "frames_to_average": 1,
            "databuffer_size": 100,
        }

        # Autofocus
        # autofocus_sample = {
        #     "coarse_range": 500,
        #     "coarse_step_size": 50,
        #     "coarse_selected": True,
        #     "fine_range": 50,
        #     "fine_step_size": 5,
        #     "fine_selected": True,
        #     "robust_fit": False,
        # }

        stage_parameters_dict_sample = {
            "limits": True,
        }
        for microscope_name in configuration["configuration"]["microscopes"].keys():
            stage_parameters_dict_sample[microscope_name] = {}
            for k in ["theta_step", "f_step", "z_step"]:
                stage_parameters_dict_sample[microscope_name][k] = configuration[
                    "configuration"
                ]["microscopes"][microscope_name]["stage"].get(k, 30)
            stage_parameters_dict_sample[microscope_name]["xy_step"] = min(
                configuration["configuration"]["microscopes"][microscope_name][
                    "stage"
                ].get("x_step", 500),
                configuration["configuration"]["microscopes"][microscope_name][
                    "stage"
                ].get("y_step", 500),
            )

        microscope_name = configuration["configuration"]["microscopes"].keys()[0]
        zoom = configuration["configuration"]["microscopes"][microscope_name]["zoom"][
            "position"
        ].keys()[0]
        microscope_parameters_dict_sample = {
            "microscope_name": microscope_name,
            "image_mode": "live",
            "zoom": zoom,
            "stack_cycling_mode": "per_stack",
            "start_position": 0.0,
            "end_position": 100.0,
            "step_size": 20.0,
            "number_z_steps": 5,
            "timepoints": 1,
            "stack_pause": 0.0,
            "is_save": False,
            "stack_acq_time": 1.0,
            "timepoint_interval": 0,
            "experiment_duration": 1.03,
            "is_multiposition": False,
            "multiposition_count": 1,
            "selected_channels": 0,
            "stack_z_origin": 0,
            "stack_focus_origin": 0,
            "start_focus": 0.0,
            "end_focus": 0.0,
            "abs_z_start": 0.0,
            "abs_z_end": 100.0,
            "scanrange": 500.0,
            "n_plane": 1.0,
            "offset_start": 0.0,
            "offset_end": 9.8,
            "conpro_cycling_mode": "per_stack",
            "waveform_template": "Default",
        }

        multipositions_sample = [
            {"x": 10.0, "y": 10.0, "z": 10.0, "f": 10.0, "theta": 10.0}
        ]

        self.experiment_sample = {
            "Saving": saving_dict_sample,
            "CameraParameters": camera_parameters_dict_sample,
            "StageParameters": stage_parameters_dict_sample,
            "MicroscopeState": microscope_parameters_dict_sample,
            "MultiPositions": multipositions_sample,
        }

    def tearDown(self):
        delete_folder(self.test_root)
        self.manager.shutdown()

    def assert_equal_dict(self, dict1, dict2):
        # dict1 and dict2 are not nested dict
        for k in dict1.keys():
            assert dict1[k] == dict2[k], f"{k}: {dict1[k]} -- {dict2[k]}"

    def test_load_empty_experiment_file(self):
        experiment_file_path = os.path.join(self.test_root, "experiment.yml")
        with open(experiment_file_path, "w") as f:
            f.write("")
        configuration = config.load_configs(
            self.manager,
            configuration=os.path.join(self.config_path, "configuration.yaml"),
            experiment=experiment_file_path,
        )
        config.verify_experiment_config(self.manager, configuration)

        experiement_config = configuration["experiment"]
        assert type(experiement_config) == DictProxy

        # Saving parameters
        self.assert_equal_dict(
            self.experiment_sample["Saving"], experiement_config["Saving"]
        )

        # Camera parameters
        self.assert_equal_dict(
            self.experiment_sample["CameraParameters"],
            experiement_config["CameraParameters"],
        )

        # AutoFocusParameters

        # Stage parameters
        for k, value in self.experiment_sample["StageParameters"].items():
            if type(value) == dict:
                assert k in experiement_config["StageParameters"].keys()
                self.assert_equal_dict(value, experiement_config["StageParameters"][k])
            else:
                assert value == experiement_config["StageParameters"][k]

        # MicroscopeState parameters
        self.assert_equal_dict(
            self.experiment_sample["MicroscopeState"],
            experiement_config["MicroscopeState"],
        )

        # MultiPositions
        for i, position in enumerate(self.experiment_sample["MultiPositions"]):
            self.assert_equal_dict(position, experiement_config["MultiPositions"][i])

    def test_load_experiment_file_with_missing_parameters(self):
        experiment = load_yaml_file(os.path.join(self.config_path, "experiment.yml"))
        # Saving prameters
        saving_parameters = list(self.experiment_sample["Saving"].keys())
        saving_parameters_deleted = self.delete_random_entries_from_dict(
            saving_parameters, experiment["Saving"]
        )

        # Camera parameters
        camera_parameters = list(self.experiment_sample["CameraParameters"].keys())
        camera_parameters.append("img_x_pixels")
        camera_parameters.append("img_y_pixels")
        camera_parameters_deleted = self.delete_random_entries_from_dict(
            camera_parameters, experiment["CameraParameters"]
        )

        # StageParameters
        configuration = load_yaml_file(
            os.path.join(self.config_path, "configuration.yaml")
        )
        # delete limits
        if "limits" in experiment["StageParameters"].keys():
            del experiment["StageParameters"]["limits"]
        # delete part of stage parameters of one microscope
        microscope_names = list(configuration["microscopes"].keys())
        if microscope_names[0] not in experiment["StageParameters"]:
            experiment["StageParameters"][microscope_names[0]] = {
                "z_step": 100.0,
                "theta_step": 10.0,
            }
        # delete all stage parameter of another microscope
        if microscope_names[1] in experiment["StageParameters"].keys():
            del experiment["StageParameters"][microscope_names[1]]

        # MicroscopeState
        micrscope_parameters = list(self.experiment_sample["MicroscopeState"].keys())
        micrscope_parameters.append("channels")
        micrscope_parameters_deleted = self.delete_random_entries_from_dict(
            micrscope_parameters, experiment["MicroscopeState"]
        )

        save_yaml_file(self.test_root, experiment, "experiment_missing_parameters.yml")
        configuration = config.load_configs(
            self.manager,
            configuration=os.path.join(self.config_path, "configuration.yaml"),
            experiment=os.path.join(
                self.test_root, "experiment_missing_parameters.yml"
            ),
        )
        config.verify_experiment_config(self.manager, configuration)
        # verify Saving parameters are added
        for k in saving_parameters_deleted:
            assert (
                k in configuration["experiment"]["Saving"].keys()
            ), f"parameter {k} should be added to Saving parameters"

        # verify CameraParameters are added
        for k in camera_parameters_deleted:
            assert (
                k in configuration["experiment"]["CameraParameters"].keys()
            ), f"parameter {k} should be added into CameraParameters"

        # verify MicroscopeState parameters are added
        for k in micrscope_parameters_deleted:
            assert (
                k in configuration["experiment"]["MicroscopeState"].keys()
            ), f"parameter {k} should be added to MicroscopeState"

        # verify Stage parameters are added
        assert (
            "limits" in configuration["experiment"]["StageParameters"].keys()
        ), "limits should be added to Stage parameters"
        for microscope_name in microscope_names:
            for k in ["xy_step", "z_step", "f_step", "theta_step"]:
                assert (
                    k in configuration["experiment"]["StageParameters"][microscope_name]
                )

    def test_load_experiment_file_with_wrong_parameter_values(self):
        configuration = config.load_configs(
            self.manager,
            configuration=os.path.join(self.config_path, "configuration.yaml"),
            experiment=os.path.join(self.config_path, "experiment.yml"),
        )
        experiment = configuration["experiment"]
        # Saving parameters
        # check if root_directory and save_directory exist
        experiment["Saving"]["root_directory"] = self.config_path
        experiment["Saving"]["save_directory"] = os.path.join(
            self.test_root, "not_exist", "not_exist"
        )
        config.verify_experiment_config(self.manager, configuration)
        assert experiment["Saving"]["root_directory"] == self.config_path
        assert os.path.exists(experiment["Saving"]["save_directory"])
        assert experiment["Saving"]["save_directory"] != os.path.join(
            self.test_root, "not_exist", "not_exist"
        )

        # CameraParameters
        # x_pixels, y_pixels
        experiment["CameraParameters"]["x_pixels"] = -10
        experiment["CameraParameters"]["y_pixels"] = "abcd"
        config.verify_experiment_config(self.manager, configuration)
        assert (
            experiment["CameraParameters"]["x_pixels"]
            == self.experiment_sample["CameraParameters"]["x_pixels"]
        )
        assert (
            experiment["CameraParameters"]["y_pixels"]
            == self.experiment_sample["CameraParameters"]["y_pixels"]
        )
        binning = int(experiment["CameraParameters"]["binning"][0])
        assert (
            experiment["CameraParameters"]["img_x_pixels"]
            == experiment["CameraParameters"]["x_pixels"] // binning
        )
        assert (
            experiment["CameraParameters"]["img_y_pixels"]
            == experiment["CameraParameters"]["y_pixels"] // binning
        )

        # binning
        for v in ["abcd", "3x3", "12.4"]:
            experiment["CameraParameters"]["binning"] = v
            config.verify_experiment_config(self.manager, configuration)
            assert experiment["CameraParameters"]["binning"] == "1x1"
            assert (
                experiment["CameraParameters"]["img_x_pixels"]
                == experiment["CameraParameters"]["x_pixels"]
            )
            assert (
                experiment["CameraParameters"]["img_y_pixels"]
                == experiment["CameraParameters"]["y_pixels"]
            )

        # sensor_mode
        experiment["CameraParameters"]["sensor_mode"] = "None"
        config.verify_experiment_config(self.manager, configuration)
        assert experiment["CameraParameters"]["sensor_mode"] == "Normal"
        experiment["CameraParameters"]["sensor_mode"] = "Lightsheet"
        config.verify_experiment_config(self.manager, configuration)
        assert experiment["CameraParameters"]["sensor_mode"] == "Normal"
        experiment["CameraParameters"]["sensor_mode"] = "Light-Sheet"
        config.verify_experiment_config(self.manager, configuration)
        assert experiment["CameraParameters"]["sensor_mode"] == "Light-Sheet"

        # readout_direction
        for v in ["abcd", 123, None]:
            experiment["CameraParameters"]["readout_direction"] = v
            config.verify_experiment_config(self.manager, configuration)
            assert (
                experiment["CameraParameters"]["readout_direction"] == "Top-to-Bottom"
            )

        experiment["CameraParameters"]["readout_direction"] = "Bottom-to-Top"
        config.verify_experiment_config(self.manager, configuration)
        assert experiment["CameraParameters"]["readout_direction"] == "Bottom-to-Top"

        # other parameters should be int
        for k in ["number_of_pixels", "databuffer_size", "frames_to_average"]:
            for v in ["abc", -10, 0]:
                experiment["CameraParameters"][k] = v
                config.verify_experiment_config(self.manager, configuration)
                assert (
                    experiment["CameraParameters"][k]
                    == self.experiment_sample["CameraParameters"][k]
                )

        # StageParameters
        experiment["StageParameters"]["limits"] = "abc"
        config.verify_experiment_config(self.manager, configuration)
        assert experiment["StageParameters"]["limits"] is True

        microscope_names = list(configuration["configuration"]["microscopes"].keys())
        for microscope_name in microscope_names:
            for k in ["xy_step", "z_step", "f_step", "theta_step"]:
                experiment["StageParameters"][microscope_name][k] = "abc"
                config.verify_experiment_config(self.manager, configuration)
                assert isinstance(
                    experiment["StageParameters"][microscope_name][k], int
                )

        # MicroscopeState
        experiment["MicroscopeState"]["microscope_name"] = "nonexist_microscope"
        config.verify_experiment_config(self.manager, configuration)
        assert experiment["MicroscopeState"]["microscope_name"] == microscope_names[0]

        experiment["MicroscopeState"]["zoom"] = "abc"
        config.verify_experiment_config(self.manager, configuration)
        assert (
            experiment["MicroscopeState"]["zoom"]
            == list(
                configuration["configuration"]["microscopes"][microscope_names[0]][
                    "zoom"
                ]["position"].keys()
            )[0]
        )

        for k in [
            "start_position",
            "end_position",
            "step_size",
            "number_z_steps",
            "timepoints",
            "stack_acq_time",
            "timepoint_interval",
            "experiment_duration",
            "stack_z_origin",
            "stack_focus_origin",
            "start_focus",
            "end_focus",
            "abs_z_start",
            "abs_z_end",
            "scanrange",
            "n_plane",
            "offset_start",
            "offset_end",
        ]:
            experiment["MicroscopeState"][k] = "nonsense_value"
            config.verify_experiment_config(self.manager, configuration)
            assert isinstance(experiment["MicroscopeState"][k], int) or isinstance(
                experiment["MicroscopeState"][k], float
            )

        # channels
        experiment["MicroscopeState"]["channels"] = [
            {
                "is_selected": True,
                "laser": "488nm",
                "laser_index": 0,
                "filter": "Empty-Alignment",
                "filter_position": 0,
                "camera_exposure_time": 200.0,
                "laser_power": 20.0,
                "interval_time": 5.0,
                "defocus": 0.0,
            }
        ]
        config.verify_experiment_config(self.manager, configuration)
        assert type(experiment["MicroscopeState"]["channels"]) is DictProxy
        assert len(list(experiment["MicroscopeState"]["channels"].keys())) == 0

        experiment["MicroscopeState"]["channels"] = {
            "channel_0": {
                "is_selected": True,
                "laser": "488nm",
                "laser_index": 0,
                "filter": "Empty-Alignment",
                "filter_position": 0,
                "camera_exposure_time": 200.0,
                "laser_power": 20.0,
                "interval_time": 5.0,
                "defocus": 0.0,
            }
        }
        config.verify_experiment_config(self.manager, configuration)
        assert type(experiment["MicroscopeState"]["channels"]) is DictProxy
        assert len(list(experiment["MicroscopeState"]["channels"].keys())) == 0

        experiment["MicroscopeState"]["channels"] = {
            "channel_100": {
                "is_selected": True,
                "laser": "488nm",
                "laser_index": 0,
                "filter": "Empty-Alignment",
                "filter_position": 0,
                "camera_exposure_time": 200.0,
                "laser_power": 20.0,
                "interval_time": 5.0,
                "defocus": 0.0,
            }
        }
        config.verify_experiment_config(self.manager, configuration)
        assert type(experiment["MicroscopeState"]["channels"]) is DictProxy
        assert len(list(experiment["MicroscopeState"]["channels"].keys())) == 0

        microscope_name = experiment["MicroscopeState"]["microscope_name"]
        lasers = [
            f"{laser['wavelength']}nm"
            for laser in configuration["configuration"]["microscopes"][microscope_name][
                "lasers"
            ]
        ]
        filterwheels = list(
            configuration["configuration"]["microscopes"][microscope_name][
                "filter_wheel"
            ]["available_filters"].keys()
        )
        config.update_config_dict(
            self.manager,
            experiment["MicroscopeState"]["channels"],
            "channel_2",
            {
                "is_selected": 1,
                "laser": "48nm",
                "laser_index": -1,
                "filter": "nonexsit_filter_***",
                "filter_position": 1,
                "camera_exposure_time": -200.0,
                "laser_power": "a",
                "interval_time": -3,
                "defocus": "a",
            },
        )
        expected_value = {
            "is_selected": False,
            "laser": lasers[0],
            "laser_index": 0,
            "filter": filterwheels[0],
            "filter_position": 0,
            "camera_exposure_time": 200.0,
            "laser_power": 20.0,
            "interval_time": 0.0,
            "defocus": 0.0,
        }
        config.verify_experiment_config(self.manager, configuration)
        assert type(experiment["MicroscopeState"]["channels"]) is DictProxy
        assert "channel_2" in experiment["MicroscopeState"]["channels"].keys()
        for k in expected_value:
            assert (
                experiment["MicroscopeState"]["channels"]["channel_2"][k]
                == expected_value[k]
            )

        config.update_config_dict(
            self.manager,
            experiment["MicroscopeState"]["channels"],
            "channel_2",
            {
                "is_selected": 1,
                "laser": lasers[1],
                "laser_index": 3,
                "filter": filterwheels[2],
                "filter_position": 1,
                "camera_exposure_time": -200.0,
                "laser_power": "a",
                "interval_time": -3,
                "defocus": "a",
            },
        )
        expected_value = {
            "is_selected": False,
            "laser": lasers[1],
            "laser_index": 1,
            "filter": filterwheels[2],
            "filter_position": 2,
            "camera_exposure_time": 200.0,
            "laser_power": 20.0,
            "interval_time": 0.0,
            "defocus": 0.0,
        }
        config.verify_experiment_config(self.manager, configuration)
        assert type(experiment["MicroscopeState"]["channels"]) is DictProxy
        assert "channel_2" in experiment["MicroscopeState"]["channels"].keys()
        for k in expected_value:
            assert (
                experiment["MicroscopeState"]["channels"]["channel_2"][k]
                == expected_value[k]
            )

        # selected_channels
        assert experiment["MicroscopeState"]["selected_channels"] == 0
        experiment["MicroscopeState"]["channels"]["channel_2"]["is_selected"] = True
        config.verify_experiment_config(self.manager, configuration)
        assert experiment["MicroscopeState"]["selected_channels"] == 1

    def select_random_entries_from_list(self, parameter_list):
        n = random.randint(1, len(parameter_list))
        return random.choices(parameter_list, k=n)

    def delete_random_entries_from_dict(self, parameter_list, parameter_dict):
        n = random.randint(1, len(parameter_list))
        deleted_parameters = random.choices(parameter_list, k=n)
        for k in deleted_parameters:
            if k in parameter_dict.keys():
                del parameter_dict[k]
        return deleted_parameters
