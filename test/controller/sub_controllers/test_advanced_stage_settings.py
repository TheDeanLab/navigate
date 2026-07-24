import os
from unittest.mock import MagicMock, patch

from navigate.config.config import get_navigate_path
from navigate.controller.sub_controllers.stages_advanced import (
    AdvancedStageParametersController,
)


def test_save_stage_parameters_writes_to_parent_configuration_path(dummy_controller):
    controller = AdvancedStageParametersController.__new__(
        AdvancedStageParametersController
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
    dummy_controller.execute = MagicMock()

    controller.parent_controller = dummy_controller
    controller.current_microscope = microscope_name
    controller.stage_dict = (
        dummy_controller.configuration["configuration"]["microscopes"][microscope_name][
            "stage"
        ].copy()
    )

    with patch(
        "navigate.controller.sub_controllers.stages_advanced.update_config_dict"
    ) as mock_update_config_dict, patch(
        "navigate.controller.sub_controllers.stages_advanced.write_to_yaml"
    ) as mock_write_to_yaml:
        controller.save_stage_parameters()

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
    dummy_controller.execute.assert_called_once_with(
        "update_stage_limits", microscope_name
    )