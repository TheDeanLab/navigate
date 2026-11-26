import tkinter as tk
from unittest.mock import MagicMock, patch

from navigate.view.main_window_content.stage_tab import StageControlTab
from navigate.view.popups.stages_advanced_popup import AdvancedStageParametersPopup


def test_load_images_binds_photoimage_to_stage_tab_master():
    stage_tab = StageControlTab.__new__(StageControlTab)
    image_stub = MagicMock()
    image_stub.subsample.return_value = MagicMock()

    with patch(
        "navigate.view.main_window_content.stage_tab.tk.PhotoImage",
        return_value=image_stub,
    ) as mock_photo_image:
        StageControlTab.load_images(stage_tab)

    assert mock_photo_image.call_count == 16
    for call in mock_photo_image.call_args_list:
        assert call.kwargs["master"] is stage_tab
        assert "file" in call.kwargs


def test_refresh_indicator_and_shortcut_layout(tk_root):
    window = tk.Toplevel(tk_root)
    view = StageControlTab(window)
    view.pack(fill="both", expand=True)
    try:
        tk_root.update_idletasks()
        positions = view.position_frame
        lamp = positions.polling_indicator
        assert positions.cget("text") == "Stage Positions"
        assert lamp.winfo_x() > positions.winfo_width() / 2
        positions.set_polling_indicator(False, "Off")
        off_color = lamp.itemcget(positions._polling_lamp, "fill")
        positions.set_polling_indicator(True, "Refreshed")
        assert lamp.itemcget(positions._polling_lamp, "fill") != off_color
        assert lamp.hover.getdescription() == "Refreshed"
        assert view.settings_shortcuts.master is view.stack_shortcuts.master
        assert (
            view.settings_shortcuts.grid_info()["row"]
            > view.stack_shortcuts.grid_info()["row"]
        )
    finally:
        window.destroy()


def test_polling_checkbox_is_beside_stage_limits_and_survives_repopulation(tk_root):
    view = AdvancedStageParametersPopup(tk_root)
    try:
        for _ in range(2):
            view.clear_view()
            view.populate_view(["x"], {"x": 0}, {"x": 100}, {}, {}, {})
            assert view.stage_polling_enabled.master is view.stage_limits_enabled.master
            assert view.stage_polling_enabled.grid_info()["column"] == 1
            assert view.stage_limits_enabled.grid_info()["column"] == 0
            view.stage_polling_enabled.configure(state="disabled")
            view.stage_polling_enabled.invoke()
            assert view.enable_stage_polling_var.get() is False
    finally:
        view.popup.destroy()
