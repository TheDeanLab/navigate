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


def test_label_input_checkbutton_honors_left_label_position(tk_root):
    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput

    label_input = LabelInput(
        tk_root,
        label_pos="left",
        label="Flip XY",
        input_class=ttk.Checkbutton,
        input_var=tk.BooleanVar(master=tk_root),
    )
    tk_root.update_idletasks()

    assert isinstance(label_input.label, ttk.Label)
    assert label_input.label.cget("text") == "Flip XY"
    assert isinstance(label_input.widget, ttk.Checkbutton)
    assert label_input.widget.cget("text") == ""
    assert int(label_input.label.grid_info()["column"]) == 0
    assert int(label_input.widget.grid_info()["column"]) == 1


def test_label_input_button_keeps_inline_text_when_left_aligned(tk_root):
    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput

    label_input = LabelInput(
        tk_root,
        label_pos="left",
        label="Apply",
        input_class=ttk.Button,
    )
    tk_root.update_idletasks()

    assert label_input.label is None
    assert label_input.widget.cget("text") == "Apply"
    assert int(label_input.widget.grid_info()["column"]) == 0


def test_widget_input_adapter_exposes_label_input_style_accessors(tk_root):
    from navigate.view.custom_widgets.LabelInputWidgetFactory import WidgetInputAdapter

    label = ttk.Label(tk_root, text="Flip XY")
    variable = tk.BooleanVar(master=tk_root, value=False)
    widget = ttk.Checkbutton(tk_root, variable=variable)
    adapter = WidgetInputAdapter(widget, variable=variable, label=label)

    adapter.set(True)

    assert adapter.master == tk_root
    assert adapter.label is label
    assert adapter.get() is True
    assert adapter.get_variable() is variable
