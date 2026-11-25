"""Real Tk edits, proxy updates and the unchanged experiment-saving lifecycle."""

import copy
import multiprocessing
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml

from navigate.config.camera_settings import seed_camera_defaults
from navigate.config.config import update_config_dict
from navigate.tools.common_functions import copy_proxy_object
from navigate.tools.file_functions import save_yaml_file
from test.controller.sub_controllers import test_scan_correction_popup as popup_tests
from test.model.devices.camera.test_hamamatsu_outputs import (
    HamamatsuOutputTriggers,
    OutputSDK,
    selections,
    normalize_outputs,
)

popup = popup_tests.popup


@pytest.fixture
def output_popup(popup, tmp_path):
    c = popup
    with multiprocessing.Manager() as manager:
        parent = c.parent_controller
        parent.manager = manager
        parent.configuration = manager.dict()
        update_config_dict(
            manager,
            parent.configuration,
            "experiment",
            {
                "CameraParameters": {
                    "scope": {
                        "scan_speed": 2,
                        "bit_depth": 12,
                        "defect_correction": 2,
                        "hot_pixel_correction": 1,
                    }
                },
            },
        )
        update_config_dict(
            manager,
            parent.configuration,
            "configuration",
            {
                "microscopes": {
                    "scope": {"camera": {"hardware": {"type": "HamamatsuOrcaQuest"}}}
                }
            },
        )
        c.camera_dict = copy_proxy_object(
            parent.configuration["configuration"]["microscopes"]["scope"]["camera"]
        )
        parent.configuration_path = tmp_path / "configuration.yaml"
        parent.configuration_controller = Mock()
        c.view.inputs["cooling"].set("On")
        c.view.inputs["trigger_source"].set("External")
        sdk = OutputSDK()
        outputs = HamamatsuOutputTriggers(sdk)
        result = dict(popup_tests.response(c), output_triggers=outputs.capabilities())
        c._receive_bit_depth(result)
        c.test_sdk = sdk
        c.test_outputs = outputs
        yield c


def edit_outputs(c):
    panel = c._output_panel
    for number, fields in selections()["connectors"].items():
        for name, value in fields.items():
            _, variable, cap = panel.fields[number, name]
            variable.set(cap["choices"].get(value, str(value)))


def confirm_outputs(c):
    """Simulate only model delivery; actual model transactions have separate tests."""
    request = c.parent_controller.execute.call_args.args[1]
    confirmed = c.test_outputs.apply(request["value"])
    c.parent_controller.configuration["experiment"]["CameraParameters"]["scope"][
        "output_triggers"
    ] = confirmed
    c._receive_bit_depth(
        dict(
            microscope="scope",
            request_id=request["request_id"],
            identity=(1,),
            error=None,
            outputs_only=True,
            output_triggers=c.test_outputs.capabilities(),
        )
    )


def test_three_real_tabs_edit_without_io_and_apply_once(output_popup):
    c = output_popup
    panel = c._output_panel
    assert [panel.notebook.tab(tab, "text") for tab in panel.notebook.tabs()] == [
        "TIMING 1",
        "TIMING 2",
        "TIMING 3",
    ]
    edit_outputs(c)
    assert c.test_sdk.writes == []
    c.parent_controller.execute.assert_not_called()
    assert str(panel.fields["2", "pulse_width_s"][0]["state"]) == "disabled"
    assert str(panel.fields["3", "pulse_width_s"][0]["state"]) == "normal"
    c.apply_output_triggers()
    request = c.parent_controller.execute.call_args.args[1]
    assert request["identity"] == (1,)
    assert set(request["value"]["connectors"]) == {"1", "2", "3"}
    assert all(
        str(widget["state"]) == "disabled" for widget, _, _ in panel.fields.values()
    )
    confirm_outputs(c)
    assert not panel.dirty
    assert not c.parent_controller.configuration_path.exists()


@pytest.mark.parametrize("number", [1, 2, 3])
def test_apply_outputs_and_refresh_keep_selected_timing_tab(output_popup, number):
    c = output_popup
    panel = c._output_panel
    panel.notebook.select(number - 1)
    edit_outputs(c)
    c.apply_output_triggers()
    confirm_outputs(c)
    assert panel.notebook.tab(panel.notebook.select(), "text") == f"TIMING {number}"
    c._receive_bit_depth(
        dict(popup_tests.response(c), output_triggers=c.test_outputs.capabilities())
    )
    assert panel.notebook.tab(panel.notebook.select(), "text") == f"TIMING {number}"


def test_selected_output_uses_connector_identity_when_tabs_change(output_popup):
    panel = output_popup._output_panel
    panel.notebook.select(2)
    capabilities = output_popup.test_outputs.capabilities()
    del capabilities["connectors"]["1"]
    panel.populate(capabilities)
    assert panel.notebook.tab(panel.notebook.select(), "text") == "TIMING 3"
    del capabilities["connectors"]["3"]
    panel.populate(capabilities)
    assert panel.notebook.tab(panel.notebook.select(), "text") == "TIMING 2"


@pytest.mark.parametrize("number", [1, 2, 3])
def test_apply_reuses_controls_without_geometry_changes(output_popup, number):
    c = output_popup
    panel = c._output_panel
    window = c.view.popup
    panel.notebook.select(number - 1)
    window.update()
    tabs = panel.notebook.tabs()
    controls = {
        key: (widget, variable) for key, (widget, variable, _) in panel.fields.items()
    }
    initial_size = (window.winfo_width(), window.winfo_height())
    initial_request = (window.winfo_reqwidth(), window.winfo_reqheight())
    configure_sizes = []
    window.bind(
        "<Configure>",
        lambda event: (
            configure_sizes.append((event.width, event.height))
            if event.widget == window
            else None
        ),
        add="+",
    )

    for action in (
        lambda: edit_outputs(c),
        c.apply_output_triggers,
        lambda: confirm_outputs(c),
    ):
        action()
        window.update()
        assert (window.winfo_width(), window.winfo_height()) == initial_size
        assert (window.winfo_reqwidth(), window.winfo_reqheight()) == initial_request
        assert panel.notebook.tabs() == tabs
        assert {
            key: (widget, variable)
            for key, (widget, variable, _) in panel.fields.items()
        } == controls
    assert all(size == initial_size for size in configure_sizes)
    assert not panel.dirty and not panel.edited
    assert panel.notebook.tab(panel.notebook.select(), "text") == f"TIMING {number}"


def test_refresh_updates_capabilities_in_place_without_marking_user_edit(output_popup):
    panel = output_popup._output_panel
    capabilities = output_popup.test_outputs.capabilities()
    controls = {
        key: (widget, variable) for key, (widget, variable, _) in panel.fields.items()
    }
    fields = capabilities["connectors"]["1"]
    fields["kind"].update(
        current="programmable", choices={"programmable": "Timed pulse"}
    )
    fields["delay_s"].update(current=0.002, maximum=2, step=0.001, writable=False)
    panel.populate(capabilities)
    assert {
        key: (widget, variable) for key, (widget, variable, _) in panel.fields.items()
    } == controls
    assert tuple(panel.fields["1", "kind"][0]["values"]) == ("Timed pulse",)
    assert panel.fields["1", "kind"][1].get() == "Timed pulse"
    assert panel.fields["1", "delay_s"][1].get() == "0.002"
    assert str(panel.fields["1", "delay_s"][0]["state"]) == "disabled"
    assert panel._range_labels["1", "delay_s"]["text"] == "Range 0 to 2; step 0.001"
    assert not panel.dirty and not panel.edited
    panel.fields["1", "delay_s"][1].set("0.003")
    assert panel.dirty and panel.edited


def test_long_status_is_scrollable_without_resizing(output_popup):
    panel = output_popup._output_panel
    window = output_popup.view.popup
    window.update()
    size = (window.winfo_reqwidth(), window.winfo_reqheight())
    message = "\n".join(f"Output validation detail {number}" for number in range(30))
    panel.status.set(message)
    window.update()
    assert (window.winfo_reqwidth(), window.winfo_reqheight()) == size
    assert panel.status_text.get("1.0", "end-1c") == message
    assert str(panel.status_text["state"]) == "disabled"
    panel.status_text.yview_moveto(1)
    assert panel.status_text.yview()[0] > 0
    panel.status.set("Applying timing outputs…")
    window.update()
    assert panel.status_text.yview()[0] == 0
    assert (window.winfo_reqwidth(), window.winfo_reqheight()) == size


@pytest.mark.parametrize("saved", [None, "On"])
def test_fixed_cooling_does_not_send_commands_or_save_display_label(
    output_popup, saved
):
    c = output_popup
    parameters = c.parent_controller.configuration["experiment"]["CameraParameters"][
        "scope"
    ]
    if saved is not None:
        parameters["cooling"] = saved
    c.camera_setting_dict = parameters
    c.local_config_controller = SimpleNamespace(camera_config_dict={"cooling": False})
    c.set_cooling_state()
    assert c.view.inputs["cooling"].get() == "Not adjustable"
    assert str(c.view.inputs["cooling"]["state"]) == "disabled"
    c.parent_controller.execute.assert_not_called()
    assert c.save_camera_settings()
    defaults = yaml.safe_load(c.parent_controller.configuration_path.read_text())[
        "microscopes"
    ]["scope"]["camera"]["advanced_settings"]
    if saved is None:
        assert "cooling" not in parameters
        assert "cooling" not in defaults
    else:
        assert parameters["cooling"] == defaults["cooling"] == saved


def test_save_updates_proxy_and_defaults_but_never_writes_experiment(
    output_popup, tmp_path
):
    c = output_popup
    experiment_path = tmp_path / "experiment.yml"
    experiment_path.write_text("original experiment\n")
    edit_outputs(c)
    assert c.save_camera_settings() is False  # awaits the model
    assert experiment_path.read_text() == "original experiment\n"
    assert not c.parent_controller.configuration_path.exists()
    confirm_outputs(c)
    assert experiment_path.read_text() == "original experiment\n"
    disk = yaml.safe_load(c.parent_controller.configuration_path.read_text())
    defaults = disk["microscopes"]["scope"]["camera"]["advanced_settings"]
    assert defaults["cooling"] == "On"  # never YAML boolean True
    assert defaults["bit_depth"] == 12 and defaults["scan_speed"] == 2
    saved = copy_proxy_object(c.parent_controller.configuration["experiment"])
    assert (
        defaults["output_triggers"]
        == saved["CameraParameters"]["scope"]["output_triggers"]
    )
    # Acquisition/exit continue to use the existing experiment writer.
    assert save_yaml_file(
        str(tmp_path), c.parent_controller.configuration["experiment"]
    )
    loaded = yaml.safe_load(experiment_path.read_text())
    restored = normalize_outputs(loaded["CameraParameters"]["scope"]["output_triggers"])
    assert restored == saved["CameraParameters"]["scope"]["output_triggers"]
    restarted = {
        "configuration": disk,
        "experiment": {"CameraParameters": {"scope": {}}},
    }
    seed_camera_defaults(restarted)
    sdk = OutputSDK()
    confirmed = HamamatsuOutputTriggers(sdk).apply(
        restarted["experiment"]["CameraParameters"]["scope"]["output_triggers"]
    )
    assert confirmed == defaults["output_triggers"]


@pytest.mark.parametrize("state", ["acquiring", "pending", "identity"])
def test_output_writes_are_guarded_in_popup(output_popup, state):
    c = output_popup
    edit_outputs(c)
    if state == "acquiring":
        c.parent_controller.acquire_bar_controller.is_acquiring = True
    elif state == "pending":
        c._depth_pending = True
    else:
        c._depth_identity = None
    c.apply_output_triggers()
    c.parent_controller.execute.assert_not_called()


def test_rejected_output_apply_preserves_draft_and_never_saves_defaults(output_popup):
    c = output_popup
    edit_outputs(c)
    c.save_camera_settings()
    c._receive_bit_depth(
        dict(
            popup_tests.response(c),
            error="Rejected width",
            output_triggers=c.test_outputs.capabilities(),
        )
    )
    assert c._output_panel.dirty
    assert "Rejected width" in c._output_panel.status.get()
    assert not c.parent_controller.configuration_path.exists()
    assert (
        "output_triggers"
        not in c.parent_controller.configuration["experiment"]["CameraParameters"][
            "scope"
        ]
    )


def test_save_failure_preserves_previous_file_and_keeps_popup_open(
    output_popup, monkeypatch
):
    c = output_popup
    c.parent_controller.configuration_path.write_text("original\n")
    monkeypatch.setattr(
        "navigate.config.camera_settings.os.replace",
        Mock(side_effect=OSError("disk error")),
    )
    c.close_popup()
    assert c.parent_controller.configuration_path.read_text() == "original\n"
    assert c.view.popup.winfo_exists()
    assert not c._depth_closed
    assert "disk error" in c._output_panel.status.get()
    assert len(list(c.parent_controller.configuration_path.parent.iterdir())) == 1


def test_old_experiment_values_override_new_defaults(output_popup):
    c = output_popup
    edit_outputs(c)
    c.save_camera_settings()
    confirm_outputs(c)
    disk = yaml.safe_load(c.parent_controller.configuration_path.read_text())
    experiment = copy.deepcopy(selections())
    experiment["connectors"]["3"]["pulse_width_s"] = 0.008
    restarted = {
        "configuration": disk,
        "experiment": {"CameraParameters": {"scope": {"output_triggers": experiment}}},
    }
    seed_camera_defaults(restarted)
    assert (
        restarted["experiment"]["CameraParameters"]["scope"]["output_triggers"]
        == experiment
    )


def test_restart_displays_saved_outputs_until_preparation_restores_camera(output_popup):
    c = output_popup
    c.parent_controller.configuration["experiment"]["CameraParameters"]["scope"][
        "output_triggers"
    ] = selections()
    c._receive_bit_depth(
        dict(popup_tests.response(c), output_triggers=c.test_outputs.capabilities())
    )
    panel = c._output_panel
    assert panel.dirty and not panel.edited
    assert "Saved selections differ" in panel.status.get()
    for number, fields in selections()["connectors"].items():
        assert panel.selection()["connectors"][number].items() >= fields.items()
    assert c.test_sdk.writes == []
    c.test_outputs.apply(selections())  # acquisition preparation reapplies preferences
    c._receive_bit_depth(
        dict(popup_tests.response(c), output_triggers=c.test_outputs.capabilities())
    )
    assert not panel.dirty
