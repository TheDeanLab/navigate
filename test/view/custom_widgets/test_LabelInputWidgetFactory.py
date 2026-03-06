import tkinter as tk
from tkinter import ttk


class NastyVar:
    def get(self):
        raise TypeError


def _grid_padding_pair(value):
    text = str(value).strip()
    if text.startswith("(") and text.endswith(")"):
        parts = [int(part.strip()) for part in text[1:-1].split(",") if part.strip()]
    else:
        parts = [int(part) for part in text.split()]
    if len(parts) == 1:
        return (parts[0], parts[0])
    return tuple(parts)


def test_label_input_get(tk_root):
    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput

    frame = ttk.Frame(tk_root)
    frame.grid(row=0, column=0)
    label_input = LabelInput(frame)
    tk_root.update()
    assert label_input.get() == ""
    label_input.destroy()
    label_input = LabelInput(frame, input_var=NastyVar())
    tk_root.update()
    assert label_input.get() == ""
    assert label_input.get(1) == 1
    label_input.destroy()
    frame.destroy()


def test_label_input_pad_input_resolves_theme_spacing_tokens(tk_root):
    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput

    frame = ttk.Frame(tk_root)
    frame.grid(row=0, column=0)
    label_input = LabelInput(frame, label="Exposure")
    tk_root.update_idletasks()

    label_input.pad_input("space_2", "space_1", "space_3", "space_4")
    tk_root.update_idletasks()

    grid_info = label_input.widget.grid_info()
    assert _grid_padding_pair(grid_info["padx"]) == (4, 6)
    assert _grid_padding_pair(grid_info["pady"]) == (2, 8)
    label_input.destroy()
    frame.destroy()
