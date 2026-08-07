import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from navigate.config.config import get_navigate_path
from navigate.controller.sub_controllers.stages_advanced import (
    AdvancedStageParametersController,
)


def test_limit_edit_immediately_refreshes_open_autofocus_popup(dummy_controller):
    controller = AdvancedStageParametersController.__new__(
        AdvancedStageParametersController
    )
    microscope_name = dummy_controller.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    refresh_bounds = MagicMock()
    dummy_controller._refresh_autofocus_bounds = refresh_bounds
    controller.parent_controller = dummy_controller
    controller.current_microscope = microscope_name
    controller.stage_dict = {}
    controller.view = SimpleNamespace(
        spinboxes={"f_max": MagicMock(get=MagicMock(return_value="1234.5"))}
    )

    controller.update_spinboxes("f_max")

    assert controller.stage_dict["f_max"] == 1234
    assert (
        dummy_controller.configuration["configuration"]["microscopes"][
            microscope_name
        ]["stage"]["f_max"]
        == 1234
    )
    refresh_bounds.assert_called_once_with()


def test_save_stage_parameters_writes_to_parent_configuration_path(
    dummy_controller, monkeypatch
):
    controller = AdvancedStageParametersController.__new__(
        AdvancedStageParametersController
    )
    microscope_name = dummy_controller.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    legacy_configuration_path = os.path.join(
        get_navigate_path(), "config", "configuration.yaml"
    )
    configuration_path = "/tmp/custom-configuration.yml"
    update_configuration = MagicMock()
    execute = MagicMock()
    monkeypatch.setattr(
        dummy_controller, "configuration_path", configuration_path, raising=False
    )
    monkeypatch.setattr(
        dummy_controller.configuration_controller,
        "update_configuration",
        update_configuration,
    )
    monkeypatch.setattr(dummy_controller, "execute", execute)
    assert dummy_controller.configuration_path != legacy_configuration_path

    controller.parent_controller = dummy_controller
    controller.current_microscope = microscope_name
    controller.stage_dict = dummy_controller.configuration["configuration"][
        "microscopes"
    ][microscope_name]["stage"].copy()

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
    assert mock_write_to_yaml.call_args.kwargs["filename"] != legacy_configuration_path
    update_configuration.assert_called_once()
    execute.assert_called_once_with("update_stage_limits", microscope_name)
