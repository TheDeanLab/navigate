from unittest.mock import MagicMock, patch

from navigate.view.custom_widgets.ArrowLabel import ArrowLabel


def test_arrow_label_uses_theme_panel_bg_and_rgba_image():
    arrow_image = object()

    with patch(
        "navigate.view.custom_widgets.ArrowLabel.tk.Label.__init__",
        return_value=None,
    ) as label_init, patch(
        "navigate.view.custom_widgets.ArrowLabel.create_arrow_image",
        return_value=arrow_image,
    ) as create_mock, patch(
        "navigate.view.custom_widgets.ArrowLabel.ImageTk.PhotoImage",
        return_value="arrow_photo",
    ) as photo_mock, patch(
        "navigate.view.custom_widgets.ArrowLabel.ArrowLabel.configure",
    ) as configure_mock, patch(
        "navigate.view.custom_widgets.ArrowLabel.get_theme_color",
        return_value="#1a212b",
    ):
        label = ArrowLabel(
            MagicMock(),
            xys=[(0, 20), (40, 20)],
            direction="right",
            image_width=40,
            image_height=40,
        )

    _, init_kwargs = label_init.call_args
    assert init_kwargs["background"] == "#1a212b"
    assert init_kwargs["borderwidth"] == 0
    assert init_kwargs["highlightthickness"] == 0
    create_mock.assert_called_once_with([(0, 20), (40, 20)], 40, 40, "right")
    photo_mock.assert_called_once_with(arrow_image, master=label)
    configure_mock.assert_called_once_with(image="arrow_photo")
