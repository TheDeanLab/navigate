"""Unit tests for feature-list popup model operations."""

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

import navigate.controller.sub_controllers.features_popup as features_popup_module
from navigate.controller.sub_controllers.features_popup import (
    FeaturePopupController,
    FeatureListGraphController,
)
from navigate.config.configuration_schema import CollectionSpec, SettingSpec
from navigate.model.features import feature_related_functions
from navigate.model.features.base import FeatureBase
from navigate.model.features.parameter_tools import coerce_feature_parameter


def feature_names(controller):
    """Return feature names in displayed order."""
    return [feature["name"].__name__ for feature in controller.features]


def make_three_features():
    """Return three distinct feature payloads for reorder tests."""
    return [
        {"name": feature_related_functions.Snap},
        {"name": feature_related_functions.StackPause},
        {"name": feature_related_functions.WaitToContinue},
    ]


def make_feature_popup_controller(feature_record, yaml_file_name):
    """Create an edit controller with filesystem and model boundaries mocked."""
    controller = object.__new__(FeaturePopupController)
    controller.feature_list_id = 7
    controller.persist_feature_list_edits = True
    controller.view = SimpleNamespace(
        inputs={
            "content": MagicMock(get=MagicMock(return_value='[{"name": Snap,}]')),
            "feature_list_name": MagicMock(get=MagicMock(return_value="Display Name")),
        },
        popup=MagicMock(),
    )
    controller.parent_controller = SimpleNamespace(
        execute=MagicMock(),
        menu_controller=SimpleNamespace(
            _get_custom_feature_list_record=MagicMock(
                return_value=(feature_record, yaml_file_name)
            )
        ),
    )
    controller.verify_feature_list = MagicMock(return_value=[{"name": object()}])
    controller.close_child_popups = MagicMock()
    return controller


@pytest.fixture
def graph_controller():
    """Create a graph controller without Tk widgets for model-only tests."""
    controller = object.__new__(FeatureListGraphController)
    controller.features = []
    controller.feature_structure = []
    return controller


def test_terminal_feature_replaces_existing_branch(graph_controller):
    """Break and continue replace all existing branch nodes."""
    graph_controller.features = [{"name": object()}, {"name": object()}]
    graph_controller.feature_structure = [0, 1]

    graph_controller.insert_feature(1, "Break")

    assert graph_controller.features == ["break"]
    assert graph_controller.feature_structure == [0]
    assert graph_controller.build_feature_list_text() == "break"


def test_normal_feature_replaces_terminal_branch(graph_controller, monkeypatch):
    """A normal feature replaces a previous break or continue node."""

    class TestFeature:
        pass

    monkeypatch.setattr(
        feature_related_functions, "TestFeature", TestFeature, raising=False
    )
    graph_controller.features = ["continue"]
    graph_controller.feature_structure = [0]

    graph_controller.insert_feature(1, "TestFeature")

    assert graph_controller.feature_structure == [0]
    assert graph_controller.features == [{"name": TestFeature}]


def test_feature_palette_includes_only_feature_base_subclasses(monkeypatch):
    """Imported helper classes should not be displayed as feature nodes."""

    class TestFeature(FeatureBase):
        pass

    class HelperClass:
        pass

    monkeypatch.setattr(
        feature_related_functions, "UnitTestFeature", TestFeature, raising=False
    )
    monkeypatch.setattr(
        feature_related_functions, "UnitTestHelper", HelperClass, raising=False
    )

    controller = FeatureListGraphController(
        feature_list_view=None,
        feature_content_view=None,
        preview_btn=MagicMock(),
    )

    assert "UnitTestFeature" in controller.feature_names
    assert "UnitTestHelper" not in controller.feature_names
    assert "SharedList" not in controller.feature_names


def test_start_palette_drag_keeps_only_latest_palette_button_pressed(graph_controller):
    """Clicking another feature palette button clears the previous pressed state."""

    class FakePaletteButton:
        def __init__(self):
            self.state_calls = []

        def state(self, states):
            self.state_calls.append(states)

        def winfo_exists(self):
            return True

    first_button = FakePaletteButton()
    second_button = FakePaletteButton()
    graph_controller.selected_palette_button = first_button
    graph_controller.clear_selection = MagicMock()
    graph_controller.start_drag = MagicMock(return_value="break")

    result = graph_controller.start_palette_drag(
        SimpleNamespace(widget=second_button),
        "StackPause",
    )

    assert result == "break"
    assert first_button.state_calls == [["!pressed"]]
    assert graph_controller.selected_palette_button is second_button
    graph_controller.clear_selection.assert_called_once()
    graph_controller.start_drag.assert_called_once()


def test_move_feature_right_to_interior_slot_changes_order(graph_controller):
    """Moving right to an interior slot must change displayed and saved order."""
    graph_controller.features = make_three_features()
    graph_controller.feature_structure = [0, 1, 2]

    graph_controller.move_feature(0, 2)

    assert feature_names(graph_controller) == [
        "StackPause",
        "Snap",
        "WaitToContinue",
    ]
    assert graph_controller.feature_structure == [0, 1, 2]
    assert graph_controller.build_feature_list_text() == (
        '[{"name": StackPause, },{"name": Snap, },' '{"name": WaitToContinue, },]'
    )


def test_move_feature_left_changes_order(graph_controller):
    """Moving left must keep feature payloads and structure indexes synchronized."""
    graph_controller.features = make_three_features()
    graph_controller.feature_structure = [0, 1, 2]

    graph_controller.move_feature(2, 0)

    assert feature_names(graph_controller) == [
        "WaitToContinue",
        "Snap",
        "StackPause",
    ]
    assert graph_controller.feature_structure == [0, 1, 2]


def test_move_feature_into_group_joins_group(graph_controller):
    """Dropping before a grouped feature must move the node into that group."""
    graph_controller.features = make_three_features()
    graph_controller.feature_structure = ["(", 0, 1, ")", 2]

    graph_controller.move_feature(2, 1)

    assert feature_names(graph_controller) == [
        "Snap",
        "WaitToContinue",
        "StackPause",
    ]
    assert graph_controller.feature_structure == ["(", 0, 1, 2, ")"]


def test_move_feature_out_of_group_removes_single_member_group(graph_controller):
    """Moving a grouped node away must remove the resulting one-member group."""
    graph_controller.features = make_three_features()
    graph_controller.feature_structure = ["(", 0, 1, ")", 2]

    graph_controller.move_feature(1, 3)

    assert feature_names(graph_controller) == [
        "Snap",
        "WaitToContinue",
        "StackPause",
    ]
    assert graph_controller.feature_structure == [0, 1, 2]


def test_move_feature_removes_redundant_outer_group(graph_controller):
    """Collapsing an inner group also removes a parent with one child group."""
    graph_controller.features = make_three_features() + [
        {"name": feature_related_functions.Snap}
    ]
    graph_controller.feature_structure = ["(", "(", 0, 1, ")", 2, ")", 3]

    graph_controller.move_feature(2, 4)

    assert graph_controller.feature_structure == ["(", 0, 1, ")", 2, 3]


def test_update_feature_list_warns_but_loads_imported_record(monkeypatch):
    """Source-owned lists are not saved locally but can be tuned at runtime."""
    record = {
        "module_name": "ImportedFeature",
        "feature_list_name": "Display Name",
        "filename": "/tmp/imported_feature.py",
    }
    controller = make_feature_popup_controller(record, "imported-feature.yml")
    save_yaml_file = MagicMock()
    showerror = MagicMock()
    monkeypatch.setattr(features_popup_module, "get_navigate_path", lambda: "/tmp")
    monkeypatch.setattr(features_popup_module, "load_yaml_file", lambda path: record)
    monkeypatch.setattr(features_popup_module, "save_yaml_file", save_yaml_file)
    monkeypatch.setattr(features_popup_module.messagebox, "showerror", showerror)

    controller.update_feature_list()

    save_yaml_file.assert_not_called()
    controller.parent_controller.execute.assert_called_once_with(
        "load_feature", 7, '[{"name": Snap,}]'
    )
    controller.view.popup.dismiss.assert_called_once()
    showerror.assert_called_once()


def test_update_feature_list_warns_but_loads_missing_record(monkeypatch):
    """Missing sequence metadata should not prevent the runtime update."""
    controller = make_feature_popup_controller(None, None)
    save_yaml_file = MagicMock()
    showerror = MagicMock()
    monkeypatch.setattr(features_popup_module, "save_yaml_file", save_yaml_file)
    monkeypatch.setattr(features_popup_module.messagebox, "showerror", showerror)

    controller.update_feature_list()

    save_yaml_file.assert_not_called()
    controller.parent_controller.execute.assert_called_once_with(
        "load_feature", 7, '[{"name": Snap,}]'
    )
    controller.view.popup.dismiss.assert_called_once()
    showerror.assert_called_once()
    assert "missing or invalid" in showerror.call_args.kwargs["message"]


def test_update_feature_list_saves_sequence_filename_before_runtime_update(
    monkeypatch,
):
    """Confirm persists the authoritative record before updating runtime state."""
    record = {
        "module_name": None,
        "feature_list_name": "Display Name",
        "feature_list": '[{"name": StackPause,}]',
    }
    controller = make_feature_popup_controller(record, "authoritative-record.yml")
    calls = MagicMock()
    save_yaml_file = MagicMock(return_value=True)
    calls.attach_mock(save_yaml_file, "save")
    calls.attach_mock(controller.parent_controller.execute, "execute")
    monkeypatch.setattr(features_popup_module, "get_navigate_path", lambda: "/tmp")
    monkeypatch.setattr(features_popup_module, "load_yaml_file", lambda path: record)
    monkeypatch.setattr(features_popup_module, "save_yaml_file", save_yaml_file)

    controller.update_feature_list()

    assert calls.mock_calls == [
        call.save(
            "/tmp/feature_lists",
            {
                "module_name": None,
                "feature_list_name": "Display Name",
                "feature_list": '[{"name": Snap,}]',
            },
            "authoritative-record.yml",
        ),
        call.execute("load_feature", 7, '[{"name": Snap,}]'),
    ]
    controller.view.popup.dismiss.assert_called_once()


def test_update_feature_list_warns_but_loads_when_persistence_fails(monkeypatch):
    """A failed YAML write should warn while still applying runtime edits."""
    record = {
        "module_name": None,
        "feature_list_name": "Display Name",
        "feature_list": '[{"name": StackPause,}]',
    }
    controller = make_feature_popup_controller(record, "authoritative-record.yml")
    save_yaml_file = MagicMock(return_value=False)
    showerror = MagicMock()
    monkeypatch.setattr(features_popup_module, "get_navigate_path", lambda: "/tmp")
    monkeypatch.setattr(features_popup_module, "save_yaml_file", save_yaml_file)
    monkeypatch.setattr(features_popup_module.messagebox, "showerror", showerror)

    controller.update_feature_list()

    save_yaml_file.assert_called_once()
    controller.parent_controller.execute.assert_called_once_with(
        "load_feature", 7, '[{"name": Snap,}]'
    )
    controller.view.popup.dismiss.assert_called_once()
    showerror.assert_called_once()
    assert "could not be saved" in showerror.call_args.kwargs["message"]


def test_feature_parameter_values_use_declared_schema_defaults(graph_controller):
    """Declared schemas provide editor defaults and type metadata."""

    class TestFeature:
        parameter_schema = {
            "count": SettingSpec(
                int,
                default=3,
                label="Count",
                minimum=1,
                required=True,
            )
        }

        def __init__(self, model, count=1):
            pass

    args_name, args_value, schema = graph_controller.get_feature_parameter_values(
        TestFeature
    )

    assert args_name == ["count"]
    assert args_value == [3]
    assert schema["count"].value_type is int
    assert schema["count"].minimum == 1


def test_feature_parameter_values_preserve_existing_feature_args(graph_controller):
    """Saved feature-list arguments override schema defaults in the editor."""

    class TestFeature:
        parameter_schema = {"count": SettingSpec(int, default=3)}

        def __init__(self, model, count=1):
            pass

    _, args_value, _ = graph_controller.get_feature_parameter_values(
        TestFeature,
        {"name": TestFeature, "args": (9,)},
    )

    assert args_value == [9]


def test_feature_description_uses_metadata_or_docstring_summary():
    """Feature descriptions prefer explicit metadata and fall back to docstrings."""

    class FeatureWithDescription:
        feature_description = "Explicit editor summary."

    class FeatureWithDocstring:
        """First paragraph summary.

        Longer implementation notes should not crowd the editor.
        """

    class SampleFeature:
        """SampleFeature class for doing useful microscope work.

        Longer implementation notes should not crowd the editor.
        """

    class BareClassForFeature:
        """class for running a small feature.

        Longer implementation notes should not crowd the editor.
        """

    class FeatureWithoutDocstring:
        pass

    assert (
        FeatureListGraphController.get_feature_description(FeatureWithDescription)
        == "Explicit editor summary."
    )
    assert (
        FeatureListGraphController.get_feature_description(FeatureWithDocstring)
        == "First paragraph summary."
    )
    assert (
        FeatureListGraphController.get_feature_description(SampleFeature)
        == "Doing useful microscope work."
    )
    assert (
        FeatureListGraphController.get_feature_description(BareClassForFeature)
        == "Running a small feature."
    )
    assert (
        FeatureListGraphController.get_feature_description(FeatureWithoutDocstring)
        == "Feature Without Docstring"
    )


def test_feature_parameter_values_add_loaded_microscope_and_zoom_choices(
    graph_controller,
):
    """Microscope and zoom parameters receive choices from loaded configuration."""

    class TestFeature:
        parameter_schema = {
            "resolution_mode": SettingSpec(
                str,
                default="high",
                dynamic_source="microscopes",
            ),
            "zoom_value": SettingSpec(
                str,
                default="N/A",
                dynamic_source="zoom_values",
                depends_on="resolution_mode",
            ),
        }

        def __init__(self, model, resolution_mode="high", zoom_value="N/A"):
            pass

    graph_controller.configuration_controller = SimpleNamespace(
        microscope_list=["ScopeA", "ScopeB"],
        microscope_name="ScopeB",
        get_zoom_value_list=lambda microscope_name: {
            "ScopeA": ["1x"],
            "ScopeB": ["4x", "10x"],
        }[microscope_name],
    )

    args_name, args_value, schema = graph_controller.get_feature_parameter_values(
        TestFeature
    )

    assert args_name == ["resolution_mode", "zoom_value"]
    assert args_value == ["ScopeB", "4x"]
    assert schema["resolution_mode"].choices == ("ScopeA", "ScopeB")
    assert schema["zoom_value"].choices == ("4x", "10x")


def test_feature_parameter_values_use_saved_microscope_for_zoom_choices(
    graph_controller,
):
    """Saved microscope args determine the initial linked zoom options."""

    class TestFeature:
        parameter_schema = {
            "target_resolution": SettingSpec(
                str,
                default="ScopeB",
                dynamic_source="microscopes",
            ),
            "target_zoom": SettingSpec(
                str,
                default="4x",
                dynamic_source="zoom_values",
                depends_on="target_resolution",
            ),
        }

        def __init__(self, model, target_resolution="ScopeB", target_zoom="4x"):
            pass

    graph_controller.configuration_controller = SimpleNamespace(
        microscope_list=["ScopeA", "ScopeB"],
        microscope_name="ScopeB",
        get_zoom_value_list=lambda microscope_name: {
            "ScopeA": ["1x", "2x"],
            "ScopeB": ["4x"],
        }[microscope_name],
    )

    _, args_value, schema = graph_controller.get_feature_parameter_values(
        TestFeature,
        {"name": TestFeature, "args": ("ScopeA", "2x")},
    )

    assert args_value == ["ScopeA", "2x"]
    assert schema["target_resolution"].choices == ("ScopeA", "ScopeB")
    assert schema["target_zoom"].choices == ("1x", "2x")


def test_feature_parameter_values_reset_stale_saved_zoom_to_available_choice(
    graph_controller,
):
    """Linked zoom values are constrained to available zoom choices."""

    class TestFeature:
        parameter_schema = {
            "target_resolution": SettingSpec(
                str,
                default="ScopeB",
                dynamic_source="microscopes",
            ),
            "target_zoom": SettingSpec(
                str,
                default="4x",
                dynamic_source="zoom_values",
                depends_on="target_resolution",
            ),
        }

        def __init__(self, model, target_resolution="ScopeB", target_zoom="4x"):
            pass

    graph_controller.configuration_controller = SimpleNamespace(
        microscope_list=["ScopeA", "ScopeB"],
        microscope_name="ScopeB",
        get_zoom_value_list=lambda microscope_name: {
            "ScopeA": ["1x", "2x"],
            "ScopeB": ["4x"],
        }[microscope_name],
    )

    _, args_value, schema = graph_controller.get_feature_parameter_values(
        TestFeature,
        {"name": TestFeature, "args": ("ScopeA", "not-a-zoom")},
    )

    assert args_value == ["ScopeA", "1x"]
    assert schema["target_zoom"].choices == ("1x", "2x")


def test_feature_parameter_values_do_not_infer_dynamic_choices_from_names(
    graph_controller,
):
    """Dynamic choices require explicit SettingSpec metadata."""

    class TestFeature:
        parameter_schema = {
            "resolution_mode": SettingSpec(str, default="high"),
            "zoom_value": SettingSpec(str, default="N/A"),
        }

        def __init__(self, model, resolution_mode="high", zoom_value="N/A"):
            pass

    graph_controller.configuration_controller = SimpleNamespace(
        microscope_list=["ScopeA"],
        microscope_name="ScopeA",
        get_zoom_value_list=lambda microscope_name: ["1x"],
    )

    _, args_value, schema = graph_controller.get_feature_parameter_values(TestFeature)

    assert args_value == ["high", "N/A"]
    assert schema["resolution_mode"].choices is None
    assert schema["zoom_value"].choices is None


def test_feature_parameter_values_use_explicit_dynamic_metadata(graph_controller):
    """Dynamic source metadata supports non-standard parameter names."""

    class TestFeature:
        parameter_schema = {
            "scope": SettingSpec(
                str,
                default="ScopeB",
                dynamic_source="microscopes",
            ),
            "magnification": SettingSpec(
                str,
                default="4x",
                dynamic_source="zoom_values",
                depends_on="scope",
            ),
        }

        def __init__(self, model, scope="ScopeB", magnification="4x"):
            pass

    graph_controller.configuration_controller = SimpleNamespace(
        microscope_list=["ScopeA", "ScopeB"],
        microscope_name="ScopeA",
        get_zoom_value_list=lambda microscope_name: {
            "ScopeA": ["1x", "2x"],
            "ScopeB": ["4x", "10x"],
        }[microscope_name],
    )

    args_name, args_value, schema = graph_controller.get_feature_parameter_values(
        TestFeature
    )

    assert args_name == ["scope", "magnification"]
    assert args_value == ["ScopeB", "4x"]
    assert schema["scope"].choices == ("ScopeA", "ScopeB")
    assert schema["magnification"].choices == ("4x", "10x")


def test_feature_parameter_values_add_autofocus_dynamic_choices(graph_controller):
    """Autofocus-specific dynamic sources populate from loaded configuration."""

    class TestFeature:
        parameter_schema = {
            "device": SettingSpec(str, default="stage", choices=("stage",)),
            "device_ref": SettingSpec(
                str,
                default="f",
                dynamic_source="stage_axes",
            ),
            "target_channel": SettingSpec(
                str,
                default=None,
                dynamic_source="channels",
            ),
            "calibration_action": SettingSpec(
                str,
                default=None,
                dynamic_source="autofocus_calibration_actions",
            ),
            "reference_channel": SettingSpec(
                str,
                default="channel_2",
                dynamic_source="channels",
            ),
        }

        def __init__(
            self,
            model,
            device="stage",
            device_ref="f",
            target_channel=None,
            calibration_action=None,
            reference_channel="channel_2",
        ):
            pass

    graph_controller.configuration_controller = SimpleNamespace(
        configuration={
            "configuration": {
                "microscopes": {
                    "ScopeA": {
                        "stage": {
                            "hardware": [
                                {"axes": ["x", "y", "z"]},
                                {"axes": ["f"]},
                            ]
                        }
                    },
                    "ScopeB": {"stage": {"hardware": [{"axes": ["theta", "f"]}]}},
                }
            },
            "gui": {"channel_settings": {"count": 3}},
        }
    )

    _, args_value, schema = graph_controller.get_feature_parameter_values(
        TestFeature,
        {"name": TestFeature, "args": ("stage", "f", None, "capture_reference")},
    )

    assert args_value == ["stage", "f", "channel_1", "Capture Reference", "channel_2"]
    assert schema["device"].choices == ("stage",)
    assert schema["device_ref"].choices == ("x", "y", "z", "f", "theta")
    assert schema["target_channel"].choices == (
        "channel_1",
        "channel_2",
        "channel_3",
    )
    assert schema["reference_channel"].choices == (
        "channel_1",
        "channel_2",
        "channel_3",
    )
    assert schema["calibration_action"].choices == (
        "Regular",
        "Auto Defocus",
        "Capture Reference",
        "Populate Defocus",
    )
    assert schema["calibration_action"].choice_values == {
        "Regular": None,
        "Auto Defocus": "auto_defocus",
        "Capture Reference": "capture_reference",
        "Populate Defocus": "populate_defocus",
    }


def test_feature_parameter_values_add_dynamic_stage_axis_collection_fields(
    graph_controller,
):
    """Dynamic collection schemas expand to all configured stage axes."""

    class TestFeature:
        parameter_schema = {
            "offset": CollectionSpec(
                item_schema={},
                storage="single_mapping",
                dynamic_source="stage_axes",
            )
        }

        def __init__(self, model, offset=None):
            pass

    graph_controller.configuration_controller = SimpleNamespace(
        configuration={
            "configuration": {
                "microscopes": {
                    "ScopeA": {"stage": {"hardware": [{"axes": ["x", "aux"]}]}},
                    "ScopeB": {
                        "stage": {
                            "hardware": [
                                {"axes": ["theta"]},
                                {"axes": ["sample"]},
                            ]
                        }
                    },
                }
            }
        }
    )

    _, args_value, schema = graph_controller.get_feature_parameter_values(
        TestFeature,
        {"name": TestFeature, "args": ({"aux": 2.5},)},
    )

    assert tuple(schema["offset"].item_schema) == ("x", "aux", "theta", "sample")
    assert args_value == [{"x": 0, "aux": 2.5, "theta": 0, "sample": 0}]
    assert schema["offset"].item_schema["sample"].label == "Sample"


def test_feature_parameter_values_populate_microscope_state_collection(
    graph_controller,
):
    """MicroscopeState collections use loaded experiment values as defaults."""
    graph_controller.configuration_controller = SimpleNamespace(
        configuration={
            "experiment": {
                "MicroscopeState": {
                    "stack_cycling_mode": "per_z",
                    "start_position": -10.5,
                    "end_position": 20.25,
                    "step_size": 0.5,
                    "number_z_steps": 62.0,
                    "timepoints": 3,
                    "stack_pause": 1.5,
                    "start_focus": -2.0,
                    "end_focus": 2.0,
                    "channels": {
                        "channel_1": {
                            "is_selected": True,
                            "laser": "488nm",
                        }
                    },
                }
            }
        }
    )

    args_name, args_value, schema = graph_controller.get_feature_parameter_values(
        feature_related_functions.UpdateExperimentSetting,
    )
    values = args_value[0]

    assert args_name == ["experiment_parameters"]
    assert isinstance(schema["experiment_parameters"], CollectionSpec)
    assert values["MicroscopeState.stack_cycling_mode"] == "per_z"
    assert values["MicroscopeState.start_position"] == -10.5
    assert values["MicroscopeState.channels"] == {
        "channel_1": {"is_selected": True, "laser": "488nm"}
    }
    assert schema["experiment_parameters"].item_schema[
        "MicroscopeState.stack_cycling_mode"
    ].choices == ("per_stack", "per_z")
    assert (
        schema["experiment_parameters"]
        .item_schema["MicroscopeState.step_size"]
        .exclusive_minimum
        == 0
    )


def test_feature_parameter_values_keep_saved_microscope_state_overrides(
    graph_controller,
):
    """Saved MicroscopeState collection values override loaded defaults."""
    graph_controller.configuration_controller = SimpleNamespace(
        configuration={
            "experiment": {
                "MicroscopeState": {
                    "timepoints": 1,
                    "stack_pause": 0,
                }
            }
        }
    )

    _, args_value, _ = graph_controller.get_feature_parameter_values(
        feature_related_functions.UpdateExperimentSetting,
        {
            "name": feature_related_functions.UpdateExperimentSetting,
            "args": (
                {
                    "MicroscopeState.timepoints": 5,
                    "MicroscopeState.stack_pause": 7.5,
                },
            ),
        },
    )

    assert args_value[0]["MicroscopeState.timepoints"] == 5
    assert args_value[0]["MicroscopeState.stack_pause"] == 7.5


def test_refresh_linked_zoom_choices_updates_widget_and_schema(graph_controller):
    """Changing the selected microscope updates the linked zoom choices."""

    class FakeInput:
        def __init__(self, value):
            self.value = value
            self.values = []

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

        def set_values(self, values):
            self.values = tuple(values)

    microscope_input = FakeInput("ScopeA")
    zoom_input = FakeInput("stale")
    popup = SimpleNamespace(
        inputs_by_name={
            "target_resolution": microscope_input,
            "target_zoom": zoom_input,
        },
        parameter_index_by_name={"target_zoom": 1},
        parameter_specs=[
            SettingSpec(str, dynamic_source="microscopes"),
            SettingSpec(
                str,
                dynamic_source="zoom_values",
                depends_on="target_resolution",
            ),
        ],
    )
    graph_controller.configuration_controller = SimpleNamespace(
        get_zoom_value_list=lambda microscope_name: {
            "ScopeA": ["1x", "2x"],
        }[microscope_name],
    )

    graph_controller.refresh_linked_zoom_choices(
        popup,
        "target_zoom",
        "target_resolution",
    )

    assert zoom_input.values == ("1x", "2x")
    assert zoom_input.get() == "1x"
    assert popup.parameter_specs[1].choices == ("1x", "2x")


def test_refresh_linked_zoom_choices_clears_zoom_when_no_choices(graph_controller):
    """A microscope with no zoom values clears stale linked zoom state."""

    class FakeInput:
        def __init__(self, value):
            self.value = value
            self.values = ["old"]

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

        def set_values(self, values):
            self.values = tuple(values)

    microscope_input = FakeInput("ScopeA")
    zoom_input = FakeInput("stale")
    popup = SimpleNamespace(
        inputs_by_name={
            "scope": microscope_input,
            "magnification": zoom_input,
        },
        parameter_index_by_name={"magnification": 1},
        parameter_specs=[
            SettingSpec(str, dynamic_source="microscopes"),
            SettingSpec(str, dynamic_source="zoom_values", depends_on="scope"),
        ],
    )
    graph_controller.configuration_controller = SimpleNamespace(
        get_zoom_value_list=lambda microscope_name: []
    )

    graph_controller.refresh_linked_zoom_choices(
        popup,
        "magnification",
        "scope",
    )

    assert zoom_input.values == ()
    assert zoom_input.get() == ""
    assert popup.parameter_specs[1].choices == ()


def test_coerce_feature_parameter_rejects_invalid_numeric_input():
    """Validation reports malformed user input before the feature list mutates."""
    spec = SettingSpec(int, minimum=1, maximum=5, required=True)

    with pytest.raises(ValueError, match="count"):
        coerce_feature_parameter("count", "ten", spec)

    with pytest.raises(ValueError, match="no more than 5"):
        coerce_feature_parameter("count", "6", spec)

    assert coerce_feature_parameter("count", "4", spec) == 4


def test_coerce_feature_parameter_rejects_exclusive_numeric_minimum():
    """Exclusive lower bounds reject equal numeric values."""
    spec = SettingSpec(float, exclusive_minimum=0, required=True)

    with pytest.raises(ValueError, match="greater than 0"):
        coerce_feature_parameter("step_size", "0", spec)

    assert coerce_feature_parameter("step_size", "0.1", spec) == 0.1


def test_coerce_feature_parameter_supports_single_mapping_collection():
    """Fixed feature collections are coerced to nested dictionaries."""
    spec = CollectionSpec(
        item_schema={
            "coarse_selected": SettingSpec(bool, default=True),
            "coarse_range": SettingSpec(float, default=500, required=True),
        },
        storage="single_mapping",
    )

    coerced = coerce_feature_parameter(
        "scan_settings",
        {"coarse_selected": "False", "coarse_range": "250"},
        spec,
    )

    assert coerced == {"coarse_selected": False, "coarse_range": 250.0}


def test_coerce_feature_parameter_maps_choice_labels_to_saved_values():
    """Choice labels can save a separate internal value."""
    spec = SettingSpec(
        str,
        choices=("Regular", "Capture Reference"),
        choice_values={
            "Regular": None,
            "Capture Reference": "capture_reference",
        },
    )

    assert coerce_feature_parameter("calibration_action", "Regular", spec) is None
    assert (
        coerce_feature_parameter("calibration_action", "Capture Reference", spec)
        == "capture_reference"
    )


def test_update_feature_list_keeps_acquisition_configuration_runtime_only(
    monkeypatch,
):
    """Pre-acquisition configuration must not require or rewrite custom YAML."""
    controller = make_feature_popup_controller(None, None)
    controller.persist_feature_list_edits = False
    save_yaml_file = MagicMock()
    monkeypatch.setattr(features_popup_module, "save_yaml_file", save_yaml_file)

    controller.update_feature_list()

    save_yaml_file.assert_not_called()
    (
        controller.parent_controller.menu_controller._get_custom_feature_list_record
    ).assert_not_called()
    controller.parent_controller.execute.assert_called_once_with(
        "load_feature", 7, '[{"name": Snap,}]'
    )
    controller.view.popup.dismiss.assert_called_once()


def test_grouping_rejects_shared_last_node(graph_controller):
    """A node already ending a group cannot end another new group."""
    graph_controller.feature_structure = ["(", 0, 1, ")", 2]

    assert not graph_controller.is_valid_grouping(1, 2)


def test_grouping_accepts_matching_boundaries(graph_controller):
    """Features at one nesting level may be grouped."""
    graph_controller.feature_structure = [0, 1, 2]

    assert graph_controller.is_valid_grouping(0, 1)


def test_grouping_rejects_crossing_group_boundaries(graph_controller):
    """A proposed group cannot cross the boundary of an existing group."""
    graph_controller.feature_structure = ["(", 0, ")", 1]

    assert not graph_controller.is_valid_grouping(1, 3)
