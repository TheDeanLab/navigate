"""Unit tests for feature-list popup behavior."""

from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

import navigate.controller.sub_controllers.features_popup as features_popup_module
from navigate.controller.sub_controllers.features_popup import (
    FeatureListGraphController,
    FeaturePopupController,
    verify_feature_list,
)
from navigate.model.features import feature_related_functions


class TextBuffer:
    def __init__(self, value=""):
        self.value = value

    def get(self, *_args):
        return self.value

    def delete(self, *_args):
        self.value = ""

    def insert(self, *_args):
        self.value = _args[-1]


class ValueInput:
    def __init__(self, value=""):
        self.value = value
        self.widget = {}

    def get(self, *_args):
        return self.value

    def set(self, value):
        self.value = value


@pytest.fixture
def feature_popup_controller():
    controller = FeaturePopupController.__new__(FeaturePopupController)
    controller.feature_list_id = 0
    controller.feature_list_graph_controller = SimpleNamespace(
        child_popups=[],
        update=MagicMock(),
    )
    controller.view = SimpleNamespace(
        inputs={
            "content": TextBuffer("[]"),
            "feature_list_name": ValueInput("Example"),
        },
        popup=SimpleNamespace(dismiss=MagicMock()),
    )
    controller.parent_controller = SimpleNamespace(
        model=SimpleNamespace(get_feature_list=MagicMock(return_value=[{"name": "x"}])),
        menu_controller=SimpleNamespace(
            feature_list_names=["zero", "one"],
            add_feature_list=MagicMock(return_value=True),
        ),
        execute=MagicMock(),
        features_popup_controller=None,
    )
    return controller


def test_populate_feature_list_sets_name_and_updates_graph(feature_popup_controller):
    feature_popup_controller.populate_feature_list(1)

    assert feature_popup_controller.feature_list_id == 1
    assert feature_popup_controller.view.inputs["feature_list_name"].get() == "one"
    assert (
        feature_popup_controller.view.inputs["feature_list_name"].widget["state"]
        == "disabled"
    )
    feature_popup_controller.feature_list_graph_controller.update.assert_called_once_with(
        [{"name": "x"}]
    )


@patch("navigate.controller.sub_controllers.features_popup.messagebox.showerror")
def test_add_feature_list_requires_name(mock_error, feature_popup_controller):
    feature_popup_controller.verify_feature_list = MagicMock(return_value=True)
    feature_popup_controller.view.inputs["feature_list_name"].set("")

    feature_popup_controller.add_feature_list()

    mock_error.assert_called_once()
    feature_popup_controller.parent_controller.menu_controller.add_feature_list.assert_not_called()


@patch("navigate.controller.sub_controllers.features_popup.messagebox.showerror")
def test_add_feature_list_duplicate_name(mock_error, feature_popup_controller):
    feature_popup_controller.verify_feature_list = MagicMock(return_value=True)
    feature_popup_controller.view.inputs["feature_list_name"].set("Repeated")
    feature_popup_controller.parent_controller.menu_controller.add_feature_list.return_value = (
        False
    )

    feature_popup_controller.add_feature_list()

    mock_error.assert_called_once()


def test_add_feature_list_success_closes_popup(feature_popup_controller):
    feature_popup_controller.verify_feature_list = MagicMock(return_value=True)
    feature_popup_controller.view.inputs["content"] = TextBuffer("[\nitem\n]")
    feature_popup_controller.exit_func = MagicMock()

    feature_popup_controller.add_feature_list()

    feature_popup_controller.parent_controller.menu_controller.add_feature_list.assert_called_once_with(
        "Example",
        "[item]",
    )
    feature_popup_controller.exit_func.assert_called_once()


def test_verify_feature_list_method_delegates(feature_popup_controller):
    with patch(
        "navigate.controller.sub_controllers.features_popup.verify_feature_list",
        return_value=["verified"],
    ) as verify_mock:
        result = feature_popup_controller.verify_feature_list()

    assert result == ["verified"]
    verify_mock.assert_called_once_with("[]")


def test_exit_func_closes_and_removes_parent_attr(feature_popup_controller):
    feature_popup_controller.parent_controller.features_popup_controller = object()
    popup = SimpleNamespace(popup=SimpleNamespace(dismiss=MagicMock()))
    feature_popup_controller.feature_list_graph_controller.child_popups = [popup]

    feature_popup_controller.exit_func()

    popup.popup.dismiss.assert_called_once()
    feature_popup_controller.view.popup.dismiss.assert_called_once()
    assert not hasattr(
        feature_popup_controller.parent_controller, "features_popup_controller"
    )


def test_cancel_acquisition_marks_flag_and_dismisses(feature_popup_controller):
    popup = SimpleNamespace(popup=SimpleNamespace(dismiss=MagicMock()))
    feature_popup_controller.feature_list_graph_controller.child_popups = [popup]

    feature_popup_controller.cancel_acquisition()

    assert feature_popup_controller.start_acquisiton_flag is False
    popup.popup.dismiss.assert_called_once()
    feature_popup_controller.view.popup.dismiss.assert_called_once()


def test_flatten_feature_list_records_structure():
    controller = FeatureListGraphController.__new__(FeatureListGraphController)
    controller.features = []
    controller.feature_structure = []

    def example_feature(*_args):
        return None

    controller.flatten_feature_list(
        [{"name": example_feature}, "break", "continue", [{"name": example_feature}]]
    )

    assert len(controller.features) == 4
    assert controller.feature_structure[0] == 0
    assert controller.feature_structure[-1] == ")"


def test_update_and_get_feature_content():
    controller = FeatureListGraphController.__new__(FeatureListGraphController)
    controller.feature_content_view = TextBuffer("before")
    controller.build_feature_list_text = MagicMock(return_value="[after]")

    controller.update_feature_content()

    assert controller.get_feature_content() == "[after]"


def test_update_converts_list_content_and_draws():
    controller = FeatureListGraphController.__new__(FeatureListGraphController)
    controller.feature_content_view = TextBuffer("before")
    controller.draw_feature_list_graph = MagicMock()
    controller.feature_list = None
    controller.features = []
    controller.feature_structure = []
    controller.feature_list_graph_controllers_true = {}
    controller.feature_list_graph_controllers_false = {}

    with patch(
        "navigate.controller.sub_controllers.features_popup.convert_feature_list_to_str",
        return_value='[{"name": Example}]',
    ):
        controller.update([{"name": "Example"}])

    assert controller.feature_content_view.value == '[{"name": Example}]'
    controller.draw_feature_list_graph.assert_called_once_with(new_list_flag=True)


def test_draw_feature_list_graph_returns_early_for_invalid_content():
    controller = FeatureListGraphController.__new__(FeatureListGraphController)
    controller.get_feature_content = MagicMock(return_value="[broken")
    controller.feature_list_view = MagicMock()

    with patch(
        "navigate.controller.sub_controllers.features_popup.verify_feature_list",
        return_value=None,
    ):
        controller.draw_feature_list_graph(new_list_flag=True)

    controller.feature_list_view.winfo_children.assert_not_called()


def test_calculate_arrow_image_height():
    controller = FeatureListGraphController.__new__(FeatureListGraphController)
    controller.feature_structure = ["(", 0, "(", 1, ")", ")"]

    assert controller.calculate_arrow_image_height() == 140


def test_build_feature_list_text_formats_args_and_branches():
    controller = FeatureListGraphController.__new__(FeatureListGraphController)

    def feature_a(*_args):
        return None

    def feature_b(*_args):
        return None

    controller.features = [
        {
            "name": feature_a,
            "args": [None, True, 2, 3.5, {"a": 1}, "7", "abc"],
            "true": [{"name": feature_b}],
            "false": ["break"],
        }
    ]
    controller.feature_structure = [0]

    with patch(
        "navigate.controller.sub_controllers.features_popup.convert_feature_list_to_str",
        side_effect=["[true_branch]", "[false_branch]"],
    ):
        content = controller.build_feature_list_text()

    assert '"name": feature_a' in content
    assert '"args": (' in content
    assert '"true": [true_branch]' in content
    assert '"false": [false_branch]' in content


class _DummyGraphWidget:
    def __init__(self, width=228):
        self.width = width

    def bind(self, *_args, **_kwargs):
        pass

    def grid(self, *_args, **_kwargs):
        pass

    def winfo_width(self):
        return self.width

    def __setitem__(self, _key, _value):
        pass


def test_draw_feature_list_graph_uses_theme_background_for_loop_arrows():
    controller = FeatureListGraphController.__new__(FeatureListGraphController)
    controller.feature_list_view = MagicMock()
    controller.feature_list_view.winfo_children.return_value = []
    controller.board_canvas = None
    controller.marker = None
    controller.features = [
        {"name": lambda *_args: None},
        {"name": lambda *_args: None},
        {"name": lambda *_args: None},
    ]
    controller.feature_structure = [0, "(", 1, 2, ")"]

    loop_arrow_image = object()
    loop_arrow_label = MagicMock()

    with (
        patch(
            "navigate.controller.sub_controllers.features_popup.FeatureIcon",
            side_effect=lambda *_args, **_kwargs: _DummyGraphWidget(width=228),
        ),
        patch(
            "navigate.controller.sub_controllers.features_popup.ArrowLabel",
            side_effect=lambda *_args, **_kwargs: _DummyGraphWidget(width=104),
        ),
        patch(
            "navigate.controller.sub_controllers.features_popup.create_arrow_image",
            return_value=loop_arrow_image,
        ),
        patch(
            "navigate.controller.sub_controllers.features_popup.ImageTk.PhotoImage",
            return_value="loop_photo",
        ) as photo_mock,
        patch(
            "navigate.controller.sub_controllers.features_popup.tk.Label",
            return_value=loop_arrow_label,
        ) as label_mock,
        patch(
            "navigate.controller.sub_controllers.features_popup.get_theme_color",
            return_value="#1a212b",
        ),
    ):
        controller.draw_feature_list_graph(new_list_flag=False)

    photo_mock.assert_called_once_with(
        loop_arrow_image,
        master=controller.feature_list_view,
    )
    label_mock.assert_called_once_with(
        controller.feature_list_view,
        image="loop_photo",
        bg="#1a212b",
        borderwidth=0,
        highlightthickness=0,
    )
    loop_arrow_label.grid.assert_called_once()


class FakeMenu:
    def __init__(self, *_args, **_kwargs):
        self.commands = {}
        self.post_args = None

    def add_command(self, label, command):
        self.commands[label] = command

    def post(self, x_root, y_root):
        self.post_args = (x_root, y_root)


def test_show_menu_delete_feature_updates_graph():
    controller = FeatureListGraphController.__new__(FeatureListGraphController)

    def feature_a(*_args):
        return None

    def feature_b(*_args):
        return None

    controller.feature_list_view = MagicMock()
    controller.features = [{"name": feature_a}, {"name": feature_b}]
    controller.feature_structure = [0, 1]
    controller.chips = [MagicMock(), MagicMock()]
    controller.selected_chips = []
    controller.update_feature_content = MagicMock()
    controller.draw_feature_list_graph = MagicMock()
    controller.clear_selection = MagicMock()

    menu = FakeMenu()
    with patch(
        "navigate.controller.sub_controllers.features_popup.tk.Menu",
        return_value=menu,
    ):
        handler = controller.show_menu(0, flag=False)
        handler(SimpleNamespace(x_root=10, y_root=20))

    menu.commands["Delete"]()

    assert menu.post_args == (10, 20)
    assert len(controller.features) == 1
    assert controller.feature_structure == [0]
    controller.update_feature_content.assert_called_once()
    controller.draw_feature_list_graph.assert_called_once_with(False)


def test_show_menu_insert_before_and_after():
    controller = FeatureListGraphController.__new__(FeatureListGraphController)

    def feature_a(*_args):
        return None

    controller.feature_list_view = MagicMock()
    controller.features = [{"name": feature_a}]
    controller.feature_structure = [0]
    controller.chips = [MagicMock()]
    controller.selected_chips = []
    controller.update_feature_content = MagicMock()
    controller.draw_feature_list_graph = MagicMock()
    controller.clear_selection = MagicMock()

    menu = FakeMenu()
    with patch(
        "navigate.controller.sub_controllers.features_popup.tk.Menu",
        return_value=menu,
    ):
        handler = controller.show_menu(0, flag=True)
        handler(SimpleNamespace(x_root=1, y_root=2))

    menu.commands["Insert Before"]()
    assert len(controller.features) == 2
    assert controller.feature_structure == [0, 1]

    controller.features = [{"name": feature_a}]
    controller.feature_structure = [0]
    menu.commands["Insert After"]()
    assert len(controller.features) == 2
    assert controller.feature_structure == [0, 1]


def test_verify_feature_list_handles_break_and_continue():
    assert verify_feature_list("break") == ["break"]
    assert verify_feature_list("continue") == ["continue"]


@patch("navigate.controller.sub_controllers.features_popup.messagebox.showerror")
@patch("navigate.controller.sub_controllers.features_popup.convert_str_to_feature_list")
def test_verify_feature_list_shows_error_for_invalid_content(
    mock_convert,
    mock_error,
):
    mock_convert.return_value = None

    result = verify_feature_list("[not valid")

    assert result is None
    mock_error.assert_called_once()


@patch("navigate.controller.sub_controllers.features_popup.convert_str_to_feature_list")
def test_verify_feature_list_returns_converted_value(mock_convert):
    mock_convert.return_value = [{"name": "ok"}]

    result = verify_feature_list("[{'name': 'ok'}]")

    assert result == [{"name": "ok"}]


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
