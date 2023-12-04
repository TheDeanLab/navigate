import tkinter as tk


class NastyVar:
    def get(self):
        raise TypeError


def test_label_input_get():
    from navigate.view.custom_widgets.LabelInputWidgetFactory import LabelInput

    root = tk.Tk()
    label_input = LabelInput(root)
    root.update()
    assert label_input.get() == ""
    label_input = LabelInput(root, input_var=NastyVar())
    root.update()
    assert label_input.get() == ""
    assert label_input.get(1) == 1
    root.destroy()
