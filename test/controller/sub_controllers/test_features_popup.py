"""Unit tests for feature-list popup model operations."""

import pytest

from navigate.controller.sub_controllers.features_popup import (
    FeatureListGraphController,
)
from navigate.model.features import feature_related_functions


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
