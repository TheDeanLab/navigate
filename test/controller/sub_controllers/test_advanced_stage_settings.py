import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from navigate.config.config import get_navigate_path
from navigate.controller.sub_controllers.stages_advanced import (
    AdvancedStageParametersController,
)


def test_limit_edit_immediately_refreshes_open_autofocus_popup(
    dummy_controller, monkeypatch
):
    controller = AdvancedStageParametersController.__new__(
        AdvancedStageParametersController
    )
    microscope_name = dummy_controller.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    refresh_bounds = MagicMock()
    monkeypatch.setattr(
        dummy_controller,
        "_refresh_autofocus_bounds",
        refresh_bounds,
        raising=False,
    )
    stage_configuration = dummy_controller.configuration["configuration"][
        "microscopes"
    ][microscope_name]["stage"]
    monkeypatch.setitem(stage_configuration, "f_max", stage_configuration["f_max"])
    controller.parent_controller = dummy_controller
    controller.current_microscope = microscope_name
    controller.stage_dict = {}
    controller.view = SimpleNamespace(
        spinboxes={"f_max": MagicMock(get=MagicMock(return_value="1234.5"))}
    )

    controller.update_spinboxes("f_max")

    assert controller.stage_dict["f_max"] == 1234
    assert stage_configuration["f_max"] == 1234
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

    with (
        patch(
            "navigate.controller.sub_controllers.stages_advanced.update_config_dict"
        ) as mock_update_config_dict,
        patch(
            "navigate.controller.sub_controllers.stages_advanced.write_to_yaml"
        ) as mock_write_to_yaml,
    ):
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


class _Value:
    def __init__(self, value=False):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def _polling_popup(kind, enabled=True):
    controller = AdvancedStageParametersController.__new__(
        AdvancedStageParametersController
    )
    stage = {"hardware": [{"type": kind}], "position_polling": enabled}
    controller.stage_dict = stage
    controller.current_microscope = "selected"
    controller.view = SimpleNamespace(
        enable_stage_polling_var=_Value(), stage_polling_enabled=MagicMock()
    )
    controller.parent_controller = SimpleNamespace(
        args=SimpleNamespace(synthetic_hardware=False),
        configuration={
            "configuration": {"microscopes": {"selected": {"stage": stage}}}
        },
        configuration_controller=SimpleNamespace(microscope_name="selected"),
        stage_controller=SimpleNamespace(
            refresh_position_telemetry_status=MagicMock(),
            refresh_position_telemetry_settings=MagicMock(),
        ),
    )
    return controller


@pytest.mark.parametrize("kind", ["Synthetic", "ASI", "MS2000", "MFC2000"])
@pytest.mark.parametrize("enabled", [True, False])
def test_polling_checkbox_loads_supported_microscope_preference(kind, enabled):
    controller = _polling_popup(kind, enabled)
    controller.configure_stage_polling()
    assert controller.view.enable_stage_polling_var.get() is enabled
    assert (
        controller.view.stage_polling_enabled.configure.call_args.kwargs["state"]
        == "normal"
    )


def test_unsupported_polling_is_unchecked_read_only_and_preserves_config():
    controller = _polling_popup("MP285", True)
    controller.configure_stage_polling()
    assert controller.view.enable_stage_polling_var.get() is False
    assert (
        controller.view.stage_polling_enabled.configure.call_args.kwargs["state"]
        == "disabled"
    )
    controller.view.enable_stage_polling_var.set(True)
    controller.toggle_stage_polling()
    assert controller.view.enable_stage_polling_var.get() is False
    assert controller.stage_dict["position_polling"] is True


def test_polling_toggle_updates_selected_microscope_immediately(monkeypatch):
    controller = _polling_popup("ASI")
    monkeypatch.setattr(
        "navigate.controller.sub_controllers.stages_advanced.time.monotonic", lambda: 42
    )
    controller.view.enable_stage_polling_var.set(False)
    controller.toggle_stage_polling()
    assert controller.stage_dict["position_polling"] is False
    parent = controller.parent_controller
    assert (
        parent.configuration["configuration"]["microscopes"]["selected"]["stage"][
            "position_polling"
        ]
        is False
    )
    assert parent._stage_position_valid_after == 42
    parent.stage_controller.refresh_position_telemetry_status.assert_called_once()


def test_selecting_other_microscope_recalculates_support_and_preference():
    controller = _polling_popup("ASI", False)
    controller.configure_stage_polling()
    controller.stage_dict = {"hardware": [{"type": "MP285"}]}
    controller.configure_stage_polling()
    assert (
        controller.view.stage_polling_enabled.configure.call_args.kwargs["state"]
        == "disabled"
    )
    controller.stage_dict = {"hardware": [{"type": "Synthetic"}]}
    controller.configure_stage_polling()
    assert (
        controller.view.stage_polling_enabled.configure.call_args.kwargs["state"]
        == "normal"
    )
    assert controller.view.enable_stage_polling_var.get() is True
