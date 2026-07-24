import os
from unittest.mock import MagicMock, patch

from navigate.config.config import get_navigate_path
from navigate.controller.sub_controllers.camera_settings import (
    AdvancedCameraSettingController,
)


def test_save_camera_settings_writes_to_parent_configuration_path(dummy_controller):
    controller = AdvancedCameraSettingController.__new__(
        AdvancedCameraSettingController
    )
    microscope_name = dummy_controller.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    legacy_configuration_path = os.path.join(
        get_navigate_path(), "config", "configuration.yaml"
    )
    dummy_controller.configuration_path = "/tmp/custom-configuration.yml"
    assert dummy_controller.configuration_path != legacy_configuration_path
    dummy_controller.configuration_controller.update_configuration = MagicMock()

    controller.parent_controller = dummy_controller
    controller.current_microscope = microscope_name
    controller.camera_dict = (
        dummy_controller.configuration["configuration"]["microscopes"][microscope_name][
            "camera"
        ].copy()
    )
    controller.view = MagicMock()
    controller.view.inputs = {
        "trigger_source": MagicMock(get=MagicMock(return_value="External")),
        "cooling": MagicMock(get=MagicMock(return_value="Off")),
    }

    with patch(
        "navigate.controller.sub_controllers.camera_settings.update_config_dict"
    ) as mock_update_config_dict, patch(
        "navigate.controller.sub_controllers.camera_settings.write_to_yaml"
    ) as mock_write_to_yaml:
        controller.save_camera_settings()

    mock_update_config_dict.assert_called_once()
    mock_write_to_yaml.assert_called_once()
    assert (
        mock_write_to_yaml.call_args.kwargs["filename"]
        == dummy_controller.configuration_path
    )
    assert (
        mock_write_to_yaml.call_args.kwargs["filename"] != legacy_configuration_path
    )
    dummy_controller.configuration_controller.update_configuration.assert_called_once()
    camera_parameters = dummy_controller.configuration["experiment"]["CameraParameters"][
        microscope_name
    ]
    assert camera_parameters["trigger_source"] == "External"
    assert camera_parameters["cooling"] == "Off"
