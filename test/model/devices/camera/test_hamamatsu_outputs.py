"""Independent timing outputs, exact rollback, and fresh-process persistence."""

import copy
from collections import Counter
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from navigate.config.camera_settings import seed_camera_defaults
from navigate.model.devices.camera.hamamatsu_outputs import (
    COUNT,
    FIELDS,
    SHARED,
    STRIDE,
    HamamatsuOutputTriggers,
    applicable,
    normalize_outputs,
)
from test.model import test_camera_advanced_settings as model_tests
from test.model.devices.camera import test_scan_correction as scan_tests

model = model_tests.model
scan_camera = scan_tests.scan_camera
camera = scan_tests.camera
coupled_camera = scan_tests.hamamatsu_tests.coupled_camera


class OutputSDK:
    """Property-level fake with separate registers for each physical connector."""

    def __init__(self, count=3):
        self.values = {COUNT: count}
        self.ranges = {}
        self.enums = {}
        self.writes = []
        self.reject = None
        self.readonly = set()
        for n in range(1, count + 1):
            for field, (base, enum) in FIELDS.items():
                prop = base + (n - 1) * STRIDE
                if enum:
                    self.enums[prop] = tuple(enum)
                    self.ranges[prop] = (min(enum), max(enum), 1)
                    self.values[prop] = min(enum)
                else:
                    self.ranges[prop] = (
                        (1e-6 if field == "pulse_width_s" else 0),
                        10,
                        1 if field == "pre_hsync_count" else 1e-6,
                    )
                    self.values[prop] = self.ranges[prop][0]

    def get_property_value(self, prop):
        return self.values.get(prop, False)

    def get_property_range(self, prop):
        return self.ranges.get(prop, (None, None, None))

    def get_property_values(self, prop):
        return self.enums.get(prop)

    def get_property_value_text(self, prop, value):
        return None

    def is_property_writable(self, prop):
        return prop in self.ranges and prop not in self.readonly

    def prop_setvalue(self, prop, value):
        self.writes.append((prop, value))
        if self.reject == (prop, value):
            return False
        self.values[prop] = value
        return True


def selections():
    return {
        "version": 1,
        "connectors": {
            "1": {
                "kind": "programmable",
                "source": "vsync",
                "polarity": "positive",
                "delay_s": 0.0,
                "pulse_width_s": 0.002,
            },
            "2": {"kind": "trigger_ready", "polarity": "negative"},
            "3": {
                "kind": "programmable",
                "source": "readout_end",
                "polarity": "positive",
                "delay_s": 0.001,
                "pulse_width_s": 0.004,
            },
        },
    }


@pytest.mark.parametrize("count", [0, 1, 2, 3, 4])
def test_discovery_is_readonly_and_uses_reported_connector_count(count):
    sdk = OutputSDK(count)
    caps = HamamatsuOutputTriggers(sdk).capabilities()
    assert len(caps["connectors"]) == count
    assert caps["supported"] == bool(count)
    assert sdk.writes == []


def test_all_three_outputs_apply_independently_and_zero_delay_is_valid():
    sdk = OutputSDK()
    controller = HamamatsuOutputTriggers(sdk)
    confirmed = controller.apply(selections())
    assert sdk.values[0x001C0160] == 3
    assert sdk.values[0x001C0260] == 4
    assert sdk.values[0x001C0360] == 3
    assert sdk.values[0x001C0140] == 0
    assert sdk.values[0x001C0150] == 0.002
    assert sdk.values[0x001C0350] == 0.004
    before = dict(sdk.values)
    controller.apply({"version": 1, "connectors": {"2": {"kind": "low"}}})
    assert {k: v for k, v in sdk.values.items() if k != 0x001C0260} == {
        k: v for k, v in before.items() if k != 0x001C0260
    }
    assert confirmed["connectors"]["1"]["pulse_width_s"] == 0.002


@pytest.mark.parametrize(
    "kind", ["low", "high", "trigger_ready", "global_exposure", "any_row_exposure"]
)
def test_nonprogrammable_functions_do_not_write_remembered_timing(kind):
    sdk = OutputSDK()
    settings = selections()
    settings["connectors"] = {"1": dict(settings["connectors"]["1"], kind=kind)}
    confirmed = HamamatsuOutputTriggers(sdk).apply(settings)
    assert not any(
        prop in (0x001C0140, 0x001C0150, 0x001C0110) for prop, _ in sdk.writes
    )
    assert confirmed["connectors"]["1"]["pulse_width_s"] == 0.002


@pytest.mark.parametrize(
    "value", [False, float("nan"), float("inf"), -1, 11, 0.0000005]
)
def test_invalid_delay_never_leaves_partial_configuration(value):
    sdk = OutputSDK()
    original = dict(sdk.values)
    settings = selections()
    settings["connectors"]["3"]["delay_s"] = value
    with pytest.raises((ValueError, RuntimeError)):
        HamamatsuOutputTriggers(sdk).apply(settings)
    assert sdk.values == original


def test_failed_third_output_restores_all_three():
    sdk = OutputSDK()
    original = dict(sdk.values)
    sdk.reject = (0x001C0350, 0.004)
    with pytest.raises(RuntimeError, match="rejected"):
        HamamatsuOutputTriggers(sdk).apply(selections())
    assert sdk.values == original


def test_failed_restore_marks_physical_connection_unusable():
    sdk = OutputSDK()
    write = sdk.prop_setvalue

    def fail(prop, value):
        if (prop, value) in ((0x001C0350, 0.004), (0x001C0160, 1)):
            return False
        return write(prop, value)

    sdk.prop_setvalue = fail
    with pytest.raises(RuntimeError, match="restoration failed"):
        HamamatsuOutputTriggers(sdk).apply(selections())
    assert "reconnect" in sdk._advanced_settings_error
    with pytest.raises(RuntimeError, match="reconnect"):
        HamamatsuOutputTriggers(sdk).apply(selections())


def test_rollback_restores_timing_before_function_makes_it_readonly():
    sdk = OutputSDK()
    original = dict(sdk.values)
    writable = sdk.is_property_writable
    sdk.is_property_writable = lambda prop: writable(prop) and (
        prop not in (0x001C0140, 0x001C0150) or sdk.values[0x001C0160] == 3
    )
    sdk.reject = (0x001C0350, 0.004)
    with pytest.raises(RuntimeError, match="rejected"):
        HamamatsuOutputTriggers(sdk).apply(selections())
    assert sdk.values == original


def test_restore_readiness_without_assuming_programmable_support():
    sdk = OutputSDK(1)
    sdk.enums[0x001C0160] = (1, 4, 5)
    sdk.values.update({0x001C0160: 4, 0x001C0120: 2})
    controller = HamamatsuOutputTriggers(sdk)
    snapshot = controller.snapshot()
    sdk.values.update({0x001C0160: 1, 0x001C0120: 1})
    writable = sdk.is_property_writable
    sdk.is_property_writable = lambda prop: writable(prop) and (
        prop != 0x001C0120 or sdk.values[0x001C0160] == 4
    )
    controller.restore(snapshot)
    assert controller.snapshot() == snapshot


@pytest.mark.parametrize("action", ["probe", "change_depth"])
def test_pixel_type_changes_restore_all_three_outputs(coupled_camera, action):
    camera = coupled_camera
    outputs = OutputSDK()
    attach_outputs(camera, outputs)
    HamamatsuOutputTriggers(outputs).apply(selections())
    expected = dict(outputs.values)
    native = camera.camera_controller
    native.values.update(bits_per_channel=8.0, image_pixel_type=1.0)
    original = native.set_property_value

    def change(prop, value):
        result = original(prop, value)
        if prop == "image_pixel_type":
            outputs.values.update(OutputSDK().values)
        return result

    native.set_property_value = change
    if action == "probe":
        assert camera.get_advanced_setting_capabilities()["bit_depth"].choices == (
            8,
            12,
            16,
        )
    else:
        assert camera.set_bit_depth(12) == 12
    assert outputs.values == expected


@pytest.mark.parametrize("coupled", [0x001C0030, 0x001C0150])
def test_final_readback_detects_coupled_connector_and_shared_changes(coupled):
    sdk = OutputSDK()
    for prop, enum in SHARED.values():
        sdk.ranges[prop] = (min(enum), max(enum), 1)
        sdk.enums[prop] = tuple(enum)
        sdk.values[prop] = min(enum)
    original = dict(sdk.values)
    write = sdk.prop_setvalue

    def change(prop, value):
        success = write(prop, value)
        if (prop, value) == (0x001C0350, 0.004):
            sdk.values[coupled] = 2 if coupled == 0x001C0030 else 0.003
        return success

    sdk.prop_setvalue = change
    settings = selections()
    settings["shared"] = {
        "channel_sync": "1channel",
        "programmable_start": "first_readout",
    }
    with pytest.raises(RuntimeError, match="changed"):
        HamamatsuOutputTriggers(sdk).apply(settings)
    assert sdk.values == original


def test_programmable_fields_can_be_discovered_after_selecting_function():
    sdk = OutputSDK()
    settings = {"version": 1, "connectors": {"1": {"kind": "programmable"}}}
    confirmed = HamamatsuOutputTriggers(sdk).apply(settings)
    assert confirmed["connectors"]["1"]["pulse_width_s"] == 1e-6


def test_output_request_never_probes_depth_or_reallocates_buffers(model, scan_camera):
    sdk = OutputSDK()
    attach_outputs(scan_camera, sdk)
    model.active_microscope.camera = scan_camera
    identity = (id(scan_camera.camera_controller),)
    from unittest.mock import Mock

    scan_camera.get_advanced_setting_capabilities = Mock(
        side_effect=AssertionError("depth probe")
    )
    model.get_data_buffer = Mock(side_effect=AssertionError("buffer allocation"))
    result = model_tests.request(
        model, identity=identity, setting="output_triggers", value=selections()
    )
    assert result["error"] is None
    scan_camera.get_advanced_setting_capabilities.assert_not_called()
    model.get_data_buffer.assert_not_called()


def test_lightsheet_rejects_global_exposure_and_preserves_hsync_settings():
    sdk = OutputSDK()
    outputs = HamamatsuOutputTriggers(sdk, lightsheet=True)
    assert (
        "global_exposure"
        not in outputs.capabilities()["connectors"]["1"]["kind"]["choices"]
    )
    with pytest.raises(ValueError):
        outputs.apply({"version": 1, "connectors": {"1": {"kind": "global_exposure"}}})
    settings = selections()
    settings["connectors"]["1"].update(source="hsync", pre_hsync_count=4)
    outputs.apply(settings)
    assert sdk.values[0x001C0190] == 4


@pytest.mark.parametrize("readonly", [False, True])
def test_saved_global_exposure_replays_during_lightsheet_preparation(
    model, scan_camera, readonly
):
    """An untouched connector saved in Area mode must not block preparation."""
    from navigate.model.microscope import Microscope

    sdk = OutputSDK()
    kind = FIELDS["kind"][0] + STRIDE
    sdk.values[kind] = 2  # TIMING2 already reports Global exposure.
    settings = selections()
    settings["connectors"]["2"] = {"kind": "global_exposure"}
    saved = HamamatsuOutputTriggers(sdk).apply(settings)
    if readonly:
        sdk.readonly.add(kind)
    scan_camera._output_triggers = lambda: HamamatsuOutputTriggers(sdk, lightsheet=True)
    microscope = model.active_microscope
    microscope.camera = scan_camera
    microscope.configuration = model.configuration
    microscope.microscope_name = "scope"
    microscope.is_synthetic = False
    microscope.set_camera_trigger_mode = lambda: None
    microscope.set_camera_sensor_mode = lambda: None
    microscope.set_camera_roi_and_binning = lambda: True
    parameters = model.configuration["experiment"]["CameraParameters"]["scope"]
    parameters["output_triggers"] = saved
    sdk.writes.clear()

    Microscope.configure_camera(microscope)

    assert sdk.writes == []
    assert parameters["output_triggers"] == saved
    assert microscope._camera_settings_metadata["output_trigger_2_kind"] == (
        "global_exposure"
    )
    # Only a fresh matching readback permits preservation; a later hardware
    # change must not allow the old selection to bypass mode validation.
    sdk.values[kind] = 1
    with pytest.raises(ValueError, match="unsupported kind=global_exposure"):
        Microscope.configure_camera(microscope)


@pytest.mark.parametrize("name", ["pre_hsync_count", "base_sensor"])
@pytest.mark.parametrize("unreadable", [False, None, float("nan")])
@pytest.mark.parametrize("writable", [False, True])
def test_snapshot_unreadable_output_requires_readback_only_if_writable(
    name, unreadable, writable
):
    sdk = OutputSDK()
    prop = FIELDS[name][0]
    sdk.values[prop] = unreadable
    if not writable:
        sdk.readonly.add(prop)
    outputs = HamamatsuOutputTriggers(sdk)
    if writable:
        with pytest.raises(RuntimeError, match="Cannot snapshot output property"):
            outputs.apply(selections())
    else:
        snapshot = outputs.snapshot()
        assert prop not in snapshot
        assert FIELDS["kind"][0] in snapshot
        outputs.restore(snapshot)
    assert sdk.writes == []


@pytest.mark.parametrize(
    "setting,value", [("scan_speed", 2), ("defect_correction", 1), ("bit_depth", 8)]
)
def test_unreadable_readonly_output_does_not_block_other_settings(
    scan_camera, setting, value
):
    sdk = OutputSDK()
    prop = FIELDS["pre_hsync_count"][0]
    sdk.readonly.add(prop)
    sdk.values[prop] = False
    attach_outputs(scan_camera, sdk)
    if setting == "bit_depth":
        assert scan_camera.set_bit_depth(value) == value
    else:
        assert scan_camera.set_advanced_setting(setting, value) == value
    assert sdk.writes == []


def test_unchanged_replay_uses_fresh_values_without_reenumerating_capabilities(
    monkeypatch,
):
    sdk = OutputSDK()
    outputs = HamamatsuOutputTriggers(sdk)
    saved = outputs.apply(selections())
    calls = Counter()
    reads = Counter()
    for name in (
        "get_property_value",
        "get_property_range",
        "get_property_values",
        "get_property_value_text",
        "is_property_writable",
        "prop_setvalue",
    ):
        original = getattr(sdk, name)

        def counted(*args, _name=name, _original=original):
            calls[_name] += 1
            if _name == "get_property_value":
                reads[args[0]] += 1
            return _original(*args)

        monkeypatch.setattr(sdk, name, counted)
    assert outputs.apply(saved) == saved
    assert calls["prop_setvalue"] == 0
    assert calls["get_property_values"] == calls["get_property_value_text"] == 0
    assert calls["is_property_writable"] == 0
    # Budget SDK round trips, not wall time: the original replay made 412 calls.
    assert sum(calls.values()) < 120
    for number, fields in saved["connectors"].items():
        for name in fields:
            if applicable(name, fields):
                prop = FIELDS[name][0] + (int(number) - 1) * STRIDE
                assert reads[prop] >= 2  # Fresh confirmation plus final cross-check.

    # An external change is detected and corrected on the next preparation.
    sdk.values[FIELDS["pulse_width_s"][0]] = 0.006
    assert outputs.apply(saved) == saved
    assert sdk.values[FIELDS["pulse_width_s"][0]] == 0.002
    assert calls["prop_setvalue"] == 1


def test_changed_field_uses_capabilities_after_earlier_writes():
    sdk = OutputSDK()
    write = sdk.prop_setvalue
    original = dict(sdk.values)
    source = FIELDS["source"][0]

    def change(prop, value):
        result = write(prop, value)
        if prop == FIELDS["kind"][0] and value == 3:
            sdk.enums[source] = (1, 2)  # Vsync disappears in the new function.
        return result

    sdk.prop_setvalue = change
    with pytest.raises(ValueError, match="unsupported source=vsync"):
        HamamatsuOutputTriggers(sdk).apply(selections())
    assert sdk.values == original


def attach_outputs(camera, sdk):
    camera._output_triggers = lambda: HamamatsuOutputTriggers(sdk)


def test_model_commits_proxy_only_after_confirmation_without_reallocating(
    model, scan_camera
):
    sdk = OutputSDK()
    attach_outputs(scan_camera, sdk)
    model.active_microscope.camera = scan_camera
    identity = model_tests.request(model)["identity"]
    result = model_tests.request(
        model, identity=identity, setting="output_triggers", value=selections()
    )
    assert result["error"] is None
    assert result["data_buffer"] is None
    saved = copy.deepcopy(
        model.configuration["experiment"]["CameraParameters"]["scope"][
            "output_triggers"
        ]
    )
    settings = selections()
    settings["connectors"]["3"]["pulse_width_s"] = 0.006
    sdk.reject = (0x001C0350, 0.006)
    assert model_tests.request(
        model, identity=identity, setting="output_triggers", value=settings
    )["error"]
    assert (
        model.configuration["experiment"]["CameraParameters"]["scope"][
            "output_triggers"
        ]
        == saved
    )


@pytest.mark.parametrize("failure", ["busy", "stale"])
def test_model_rejects_busy_and_stale_requests_without_output_writes(
    model, scan_camera, failure
):
    sdk = OutputSDK()
    attach_outputs(scan_camera, sdk)
    model.active_microscope.camera = scan_camera
    identity = model_tests.request(model)["identity"]
    model.is_acquiring = failure == "busy"
    result = model_tests.request(
        model,
        identity=(0,) if failure == "stale" else identity,
        setting="output_triggers",
        value=selections(),
    )
    assert result["error"]
    assert sdk.writes == []


def test_configuration_defaults_do_not_replace_experiment_selection():
    config = {
        "configuration": {
            "microscopes": {
                "scope": {
                    "camera": {
                        "advanced_settings": {
                            "output_triggers": selections(),
                            "scan_speed": 1,
                        }
                    }
                }
            }
        },
        "experiment": {"CameraParameters": {"scope": {"scan_speed": 2}}},
    }
    seed_camera_defaults(config)
    assert config["experiment"]["CameraParameters"]["scope"]["scan_speed"] == 2
    config["experiment"]["CameraParameters"]["scope"]["output_triggers"]["connectors"][
        "1"
    ]["kind"] = "low"
    seed_camera_defaults(config)
    assert (
        config["configuration"]["microscopes"]["scope"]["camera"]["advanced_settings"][
            "output_triggers"
        ]["connectors"]["1"]["kind"]
        == "programmable"
    )


@pytest.mark.parametrize("with_experiment", [False, True])
def test_fresh_process_restores_all_outputs_from_defaults_or_saved_experiment(
    tmp_path, with_experiment
):
    settings = selections()
    settings["connectors"]["1"]["pulse_width_s"] = 1e-6
    config = {
        "configuration": {
            "microscopes": {
                "scope": {
                    "camera": {"advanced_settings": {"output_triggers": settings}}
                }
            }
        },
        "experiment": {
            "CameraParameters": {
                "scope": {"output_triggers": settings} if with_experiment else {}
            }
        },
    }
    path = tmp_path / "profile.yml"
    from navigate.tools.file_functions import save_yaml_file

    if with_experiment:
        assert save_yaml_file(str(tmp_path), config, path.name)
    else:
        path.write_text(yaml.safe_dump(config))
    code = """
import json, sys, yaml
from navigate.config.camera_settings import seed_camera_defaults
from navigate.model.devices.camera.hamamatsu_outputs import HamamatsuOutputTriggers
from navigate.model.devices.camera.format import CameraImageFormat
from navigate.model.microscope import Microscope
from types import SimpleNamespace
from test.model.devices.camera.test_hamamatsu_outputs import OutputSDK
config = yaml.safe_load(open(sys.argv[1]))
seed_camera_defaults(config)
sdk = OutputSDK()
microscope = Microscope.__new__(Microscope)
microscope.configuration = config
microscope.microscope_name = 'scope'
microscope.camera = SimpleNamespace(is_acquiring=False,
    set_output_triggers=HamamatsuOutputTriggers(sdk).apply,
    get_image_format=CameraImageFormat)
microscope.set_camera_trigger_mode = lambda: None
microscope.set_camera_sensor_mode = lambda: None
microscope.set_camera_roi_and_binning = lambda: True
microscope.configure_camera()
confirmed = config['experiment']['CameraParameters']['scope']['output_triggers']
print(json.dumps({'confirmed': confirmed, 'values': sdk.values,
                 'metadata': microscope._camera_settings_metadata}))
"""
    root = Path(__file__).resolve().parents[4]
    result = subprocess.run(
        [sys.executable, "-c", code, str(path)],
        cwd=root,
        env=dict(os.environ, PYTHONPATH=str(root / "src")),
        check=True,
        text=True,
        capture_output=True,
    )
    restored = json.loads(result.stdout)
    for number, fields in settings["connectors"].items():
        assert restored["confirmed"]["connectors"][number].items() >= fields.items()
    assert restored["values"][str(0x001C0260)] == 4
    assert restored["metadata"]["output_trigger_1_pulse_width_s"] == 1e-6
    assert restored["metadata"]["output_trigger_2_kind"] == "trigger_ready"
    assert restored["metadata"]["output_trigger_3_pulse_width_s"] == 0.004
    assert "output_trigger_2_delay_s" not in restored["metadata"]


def test_dcam_reinitialization_restores_every_output_register(monkeypatch):
    from test.model.devices.APIs.hamamatsu.test_hamamatsu_platform import load_api

    api, _ = load_api(monkeypatch)
    monkeypatch.setattr(api.DCAM, "__del__", lambda self: None)
    monkeypatch.setattr(api.camReg, "numCameras", 1)
    camera = api.DCAM.__new__(api.DCAM)
    camera._DCAM__iDevice = 0
    sdk = OutputSDK()
    HamamatsuOutputTriggers(sdk).apply(selections())
    original = dict(sdk.values)
    camera.get_property_value = lambda name: (
        sdk.get_property_value(name) if isinstance(name, int) else 1.0
    )
    camera.get_property_range = sdk.get_property_range
    camera.is_property_writable = lambda name: True
    camera.prop_setvalue = lambda prop, value: (
        sdk.prop_setvalue(prop, value) if prop in sdk.values else True
    )
    camera.dev_close = lambda: None

    def reopen(index):
        sdk.values.update(OutputSDK().values)
        return True

    camera.dev_open = reopen
    camera._DCAM__open_hdcamwait = lambda: True
    assert camera.reinitialize()
    assert sdk.values == original


def test_virtual_devices_keep_hardware_preferences_without_applying_outputs(
    model, scan_camera
):
    from navigate.model.microscope import Microscope

    sdk = OutputSDK()
    attach_outputs(scan_camera, sdk)
    microscope = model.active_microscope
    microscope.camera = scan_camera
    microscope.configuration = model.configuration
    microscope.microscope_name = "scope"
    microscope.is_synthetic = True
    microscope.set_camera_trigger_mode = lambda: None
    microscope.set_camera_sensor_mode = lambda: None
    microscope.set_camera_roi_and_binning = lambda: True
    parameters = model.configuration["experiment"]["CameraParameters"]["scope"]
    parameters["output_triggers"] = selections()
    Microscope.configure_camera(microscope)
    assert sdk.writes == []
    assert parameters["output_triggers"] == selections()
    assert not any(
        key.startswith("output_trigger_")
        for key in microscope._camera_settings_metadata
    )
