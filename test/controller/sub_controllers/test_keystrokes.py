from types import SimpleNamespace
from unittest.mock import MagicMock

from navigate.controller.sub_controllers.keystrokes import KeystrokeController


def build_keystroke_test_context():
    settings = MagicMock()
    settings.multiposition_tab = SimpleNamespace(
        multipoint_list=SimpleNamespace(
            pt=SimpleNamespace(rowheader=MagicMock()),
        )
    )

    main_view = SimpleNamespace(
        root=MagicMock(),
        scroll_frame=SimpleNamespace(mouse_wheel=MagicMock()),
        settings=settings,
        camera_waveform=SimpleNamespace(
            camera_tab=SimpleNamespace(canvas=MagicMock()),
            mip_tab=SimpleNamespace(canvas=MagicMock()),
        ),
    )

    parent_controller = SimpleNamespace(
        camera_view_controller=SimpleNamespace(
            left_click=MagicMock(),
            popup_menu=MagicMock(),
            mouse_wheel=MagicMock(),
        ),
        mip_setting_controller=SimpleNamespace(
            left_click=MagicMock(),
            popup_menu=MagicMock(),
            mouse_wheel=MagicMock(),
        ),
        multiposition_tab_controller=SimpleNamespace(handle_double_click=MagicMock()),
        stage_controller=SimpleNamespace(joystick_button_handler=MagicMock()),
        event_listeners={},
    )
    return main_view, parent_controller


def test_init_binds_rowheader_double_click_to_multiposition_controller(monkeypatch):
    monkeypatch.setattr(
        "navigate.controller.sub_controllers.keystrokes.platform.system",
        lambda: "Linux",
    )
    main_view, parent_controller = build_keystroke_test_context()

    controller = KeystrokeController(main_view, parent_controller)

    rowheader = main_view.settings.multiposition_tab.multipoint_list.pt.rowheader
    rowheader.bind.assert_any_call(
        "<Double-Button-1>",
        parent_controller.multiposition_tab_controller.handle_double_click,
    )
    assert controller.multi_controller is parent_controller.multiposition_tab_controller


def test_switch_tab_selects_only_existing_tab(monkeypatch):
    monkeypatch.setattr(
        "navigate.controller.sub_controllers.keystrokes.platform.system",
        lambda: "Linux",
    )
    main_view, parent_controller = build_keystroke_test_context()
    main_view.settings.index.return_value = 3

    controller = KeystrokeController(main_view, parent_controller)

    controller.switch_tab(SimpleNamespace(keysym="2"))
    main_view.settings.select.assert_called_once_with(1)

    main_view.settings.select.reset_mock()
    controller.switch_tab(SimpleNamespace(keysym="5"))
    main_view.settings.select.assert_not_called()
