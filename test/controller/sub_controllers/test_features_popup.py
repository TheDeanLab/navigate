from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from navigate.controller.sub_controllers.features_popup import (
    FeatureListGraphController,
    FeaturePopupController,
    verify_feature_list,
)


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


@patch("navigate.controller.sub_controllers.features_popup.save_yaml_file")
@patch("navigate.controller.sub_controllers.features_popup.load_yaml_file")
@patch("navigate.controller.sub_controllers.features_popup.get_navigate_path")
def test_update_feature_list_executes_and_saves_yaml_when_module_none(
    mock_get_path,
    mock_load_yaml,
    mock_save_yaml,
    feature_popup_controller,
):
    mock_get_path.return_value = "/tmp/navigate"
    mock_load_yaml.return_value = {"module_name": None}
    popup = SimpleNamespace(popup=SimpleNamespace(dismiss=MagicMock()))
    feature_popup_controller.feature_list_graph_controller.child_popups = [popup]
    feature_popup_controller.view.inputs["feature_list_name"].set("Test Name")
    feature_popup_controller.view.inputs["content"] = TextBuffer("[\nvalid\n]")
    feature_popup_controller.feature_list_id = 7
    feature_popup_controller.verify_feature_list = MagicMock(return_value=[{"ok": True}])

    feature_popup_controller.update_feature_list()

    feature_popup_controller.parent_controller.execute.assert_called_once_with(
        "load_feature",
        7,
        "[valid]",
    )
    mock_save_yaml.assert_called_once()
    assert feature_popup_controller.start_acquisiton_flag is True
    popup.popup.dismiss.assert_called_once()
    feature_popup_controller.view.popup.dismiss.assert_called_once()


@patch("navigate.controller.sub_controllers.features_popup.save_yaml_file")
@patch("navigate.controller.sub_controllers.features_popup.load_yaml_file")
@patch("navigate.controller.sub_controllers.features_popup.get_navigate_path")
def test_update_feature_list_skips_save_when_module_present(
    mock_get_path,
    mock_load_yaml,
    mock_save_yaml,
    feature_popup_controller,
):
    mock_get_path.return_value = "/tmp/navigate"
    mock_load_yaml.return_value = {"module_name": "external.module"}
    feature_popup_controller.verify_feature_list = MagicMock(return_value=[{"ok": True}])

    feature_popup_controller.update_feature_list()

    mock_save_yaml.assert_not_called()


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
    assert not hasattr(feature_popup_controller.parent_controller, "features_popup_controller")


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
    controller.update_feature_content = MagicMock()
    controller.draw_feature_list_graph = MagicMock()

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
    controller.update_feature_content = MagicMock()
    controller.draw_feature_list_graph = MagicMock()

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
