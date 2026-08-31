# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

"""Live autofocus choices must not turn saved hardware history into targets."""

from multiprocessing import Manager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from navigate.config.config import load_configs, update_config_dict
from navigate.config.preload import preload_configuration
from navigate.controller.configuration_controller import ConfigurationController
from navigate.controller.sub_controllers.autofocus import AutofocusPopupController
from navigate.tools.common_functions import copy_proxy_object
from navigate.view.popups.autofocus_setting_popup import AutofocusPopup


@pytest.fixture
def autofocus_popup(tk_root, monkeypatch):
    """Use real config/proxies/widgets, isolating only acquisition and dialogs."""
    config_dir = Path(__file__).resolve().parents[3] / "src" / "navigate" / "config"
    callback_errors = []
    monkeypatch.setattr(
        tk_root,
        "report_callback_exception",
        lambda *error: callback_errors.append(error),
    )
    showerror = Mock()
    monkeypatch.setattr(
        "navigate.controller.sub_controllers.autofocus.messagebox.showerror", showerror
    )
    with Manager() as manager:
        configuration = load_configs(
            manager,
            configuration=config_dir / "configuration.yaml",
            experiment=config_dir / "experiment.yml",
            waveform_constants=config_dir / "waveform_constants.yml",
            rest_api_config=config_dir / "rest_api_config.yml",
            waveform_templates=config_dir / "waveform_templates.yml",
            gui=config_dir / "gui_configuration.yml",
        )
        preload_configuration(manager, configuration)
        configuration["experiment"]["StageParameters"]["limits"] = False
        parent = SimpleNamespace(
            configuration=configuration,
            configuration_controller=ConfigurationController(configuration),
            event_listeners={},
            execute=Mock(),
        )
        view = AutofocusPopup(tk_root)
        controller = AutofocusPopupController(view, parent)
        try:
            yield SimpleNamespace(
                manager=manager,
                configuration=configuration,
                microscope=configuration["configuration"]["microscopes"]["Mesoscale"],
                settings=configuration["experiment"]["AutoFocusParameters"][
                    "Mesoscale"
                ],
                controller=controller,
                parent=parent,
                showerror=showerror,
            )
        finally:
            controller.close_popup()
        assert not callback_errors


def test_inactive_remote_focus_is_hidden_without_deleting_settings(autofocus_popup):
    ctx = autofocus_popup
    hardware = ctx.microscope["remote_focus"]["hardware"]
    channel = hardware["channel"]
    saved = dict(ctx.settings["remote_focus"][channel])
    hardware["type"] = "Synthetic"
    preload_configuration(ctx.manager, ctx.configuration)

    ctx.controller.populate_experiment_values()

    assert tuple(ctx.controller.widgets["device"].widget["values"]) == ("stage",)
    assert dict(ctx.settings["remote_focus"][channel]) == saved


def test_channel_changes_filter_choices_and_restore_saved_parameters(autofocus_popup):
    ctx = autofocus_popup
    hardware = ctx.microscope["remote_focus"]["hardware"]
    original_channel = hardware["channel"]
    ctx.settings["remote_focus"][original_channel]["coarse_range"] = 321
    saved = dict(ctx.settings["remote_focus"][original_channel])
    hardware["channel"] = "Dev1/ao3"
    preload_configuration(ctx.manager, ctx.configuration)

    ctx.controller.widgets["device"].set("remote_focus")

    assert tuple(ctx.controller.widgets["device_ref"].widget["values"]) == ("Dev1/ao3",)
    assert ctx.controller.widgets["device_ref"].get() == "Dev1/ao3"
    ctx.controller.populate_experiment_values()
    assert ctx.controller.widgets["device"].get() == "remote_focus"
    assert ctx.controller.widgets["device_ref"].get() == "Dev1/ao3"

    hardware["channel"] = original_channel
    preload_configuration(ctx.manager, ctx.configuration)
    ctx.controller.populate_experiment_values()

    assert tuple(ctx.controller.widgets["device_ref"].widget["values"]) == (
        original_channel,
    )
    assert ctx.controller.view.setting_vars["coarse_range"].get() == "321"
    assert dict(ctx.settings["remote_focus"][original_channel]) == saved
    assert "Dev1/ao3" in ctx.settings["remote_focus"]


def test_stage_choices_hide_stale_axes_and_keep_valid_selection(autofocus_popup):
    ctx = autofocus_popup
    update_config_dict(ctx.manager, ctx.settings["stage"], "obsolete", {})
    ctx.controller.widgets["device_ref"].set("z")

    ctx.controller.populate_experiment_values()

    assert set(ctx.controller.widgets["device_ref"].widget["values"]) == {
        "x",
        "y",
        "z",
        "theta",
        "f",
    }
    assert ctx.controller.widgets["device_ref"].get() == "z"
    assert "obsolete" in ctx.settings["stage"]


def test_showup_refreshes_microscope_without_overwriting_saved_settings(
    autofocus_popup,
):
    ctx = autofocus_popup
    saved = copy_proxy_object(ctx.settings)
    ctx.configuration["experiment"]["MicroscopeState"]["microscope_name"] = "Nanoscale"
    ctx.parent.configuration_controller.change_microscope("Nanoscale")
    ctx.configuration["experiment"]["AutoFocusParameters"]["Nanoscale"]["stage"]["f"][
        "coarse_range"
    ] = 75

    ctx.controller.showup()

    assert ctx.controller.microscope_name == "Nanoscale"
    assert ctx.controller.widgets["device"].get() == "stage"
    assert ctx.controller.widgets["device_ref"].get() == "f"
    assert ctx.controller.view.setting_vars["coarse_range"].get() == "75"
    assert str(ctx.controller.view.autofocus_btn["state"]) == "normal"
    assert copy_proxy_object(ctx.settings) == saved


def test_no_available_targets_clears_selection_and_disables_start(autofocus_popup):
    ctx = autofocus_popup
    for stage in ctx.microscope["stage"]["hardware"]:
        stage["axes"] = []
    ctx.microscope["remote_focus"]["hardware"]["type"] = "Synthetic"

    ctx.controller.populate_experiment_values()

    for field in ("device", "device_ref"):
        assert tuple(ctx.controller.widgets[field].widget["values"]) == ()
        assert ctx.controller.widgets[field].get() == ""
    assert str(ctx.controller.view.autofocus_btn["state"]) == "disabled"
    ctx.controller.view.setting_vars["coarse_range"].set(123)
    assert "" not in ctx.settings
    ctx.controller.start_autofocus()
    ctx.showerror.assert_called_once()
    ctx.parent.execute.assert_not_called()


@pytest.mark.parametrize("change", ["type", "channel", "axis", "microscope"])
def test_start_rechecks_target_before_any_acquisition_side_effect(
    autofocus_popup, change
):
    ctx = autofocus_popup
    if change in {"type", "channel"}:
        ctx.controller.widgets["device"].set("remote_focus")
        ctx.controller.widgets["device_ref"].set(
            ctx.microscope["remote_focus"]["hardware"]["channel"]
        )
    else:
        ctx.controller.widgets["device_ref"].set("z")
    state = ctx.configuration["experiment"]["MicroscopeState"]
    if change == "type":
        ctx.microscope["remote_focus"]["hardware"]["type"] = "Synthetic"
    elif change == "channel":
        ctx.microscope["remote_focus"]["hardware"]["channel"] = "Dev1/ao3"
    elif change == "axis":
        for stage in ctx.microscope["stage"]["hardware"]:
            stage["axes"] = [axis for axis in stage["axes"] if axis != "z"]
    else:
        state["microscope_name"] = "Nanoscale"
        ctx.parent.configuration_controller.change_microscope("Nanoscale")
    before = copy_proxy_object(state)
    defocus = {key: channel["defocus"] for key, channel in state["channels"].items()}

    ctx.controller.start_autofocus()

    ctx.showerror.assert_called_once()
    ctx.parent.execute.assert_not_called()
    assert copy_proxy_object(state) == before
    assert {
        key: channel["defocus"] for key, channel in state["channels"].items()
    } == defocus
    assert ctx.controller.acquisition_state == "idle"
    assert not ctx.controller.autofocus_active


@pytest.mark.parametrize("device_type", ["NI", "ni.NI"])
def test_current_ni_aliases_and_synthetic_stage_remain_available(
    autofocus_popup, device_type
):
    ctx = autofocus_popup
    ctx.microscope["remote_focus"]["hardware"]["type"] = device_type
    for stage in ctx.microscope["stage"]["hardware"]:
        stage["type"] = "synthetic.Synthetic"

    ctx.controller.populate_experiment_values()

    assert set(ctx.controller.widgets["device"].widget["values"]) == {
        "stage",
        "remote_focus",
    }
    assert ctx.controller.widgets["device_ref"].get() == "f"
    ctx.controller.start_autofocus()
    ctx.showerror.assert_not_called()
    assert ctx.parent.execute.call_args.args[:3] == ("autofocus", "stage", "f")
