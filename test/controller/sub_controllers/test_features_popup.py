"""Unit tests for feature-list popup model operations."""

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

import navigate.controller.sub_controllers.features_popup as features_popup_module
from navigate.controller.sub_controllers.features_popup import (
    FeaturePopupController,
    FeatureListGraphController,
)
from navigate.model.features import feature_related_functions


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


def test_move_feature_out_of_group_preserves_other_membership(graph_controller):
    """Moving a grouped node to the end must not pull another node into its group."""
    graph_controller.features = make_three_features()
    graph_controller.feature_structure = ["(", 0, 1, ")", 2]

    graph_controller.move_feature(1, 3)

    assert feature_names(graph_controller) == [
        "Snap",
        "WaitToContinue",
        "StackPause",
    ]
    assert graph_controller.feature_structure == ["(", 0, ")", 1, 2]


def test_update_feature_list_rejects_imported_record(monkeypatch):
    """Confirm must not mutate runtime state for a source-owned feature list."""
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
    controller.parent_controller.execute.assert_not_called()
    controller.view.popup.dismiss.assert_not_called()
    showerror.assert_called_once()


def test_update_feature_list_rejects_missing_record(monkeypatch):
    """Confirm must fail closed if the selected sequence record disappears."""
    controller = make_feature_popup_controller(None, None)
    save_yaml_file = MagicMock()
    showerror = MagicMock()
    monkeypatch.setattr(features_popup_module, "save_yaml_file", save_yaml_file)
    monkeypatch.setattr(features_popup_module.messagebox, "showerror", showerror)

    controller.update_feature_list()

    save_yaml_file.assert_not_called()
    controller.parent_controller.execute.assert_not_called()
    controller.view.popup.dismiss.assert_not_called()
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


def test_update_feature_list_stays_open_when_persistence_fails(monkeypatch):
    """A failed YAML write must not look like a successful editor update."""
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
    controller.parent_controller.execute.assert_not_called()
    controller.view.popup.dismiss.assert_not_called()
    showerror.assert_called_once()
    assert "could not be saved" in showerror.call_args.kwargs["message"]


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
