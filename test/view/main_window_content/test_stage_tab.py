from unittest.mock import MagicMock, patch

from navigate.view.main_window_content.stage_tab import StageControlTab


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
