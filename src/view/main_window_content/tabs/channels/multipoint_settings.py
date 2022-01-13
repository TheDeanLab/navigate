import tkinter as tk
from tkinter import ttk
from tkinter.constants import NSEW

import pandas as pd
from pandastable import Table


class multipoint_frame(ttk.Frame):
    def __init__(multipoint_frame, settings_tab, *args, **kwargs):

        # Init Frame
        ttk.Frame.__init__(multipoint_frame, settings_tab, *args, **kwargs)

        text_label = 'Multi-position Acquisition'
        ttk.Labelframe.__init__(multipoint_frame, settings_tab, text=text_label, *args, **kwargs)

        # Save Data Label
        label_position = 0
        input_position = 4
        multipoint_frame.laser_label = ttk.Label(multipoint_frame, text='Enable')
        multipoint_frame.laser_label.grid(row=0, column=label_position, sticky=(NSEW))

        # Save Data Checkbox
        on_off = tk.StringVar()
        multipoint_frame.save_check = ttk.Checkbutton(
            multipoint_frame,
            text='',
            variable=on_off
            # command=
            # onvalue=
            # offvalue=
            # state=
            # instate=
        )
        multipoint_frame.save_check.grid(row=0, column=input_position, sticky=(NSEW))

class multipoint_list(ttk.Frame):
    """
    Exploring using a pandastable for embedding an interactive list within a tk Frame.
    https://pandastable.readthedocs.io/en/latest/
    """
    def __init__(multipoint_frame, settings_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(multipoint_frame, settings_tab, *args, **kwargs)

        df = pd.DataFrame({
            'X': [0],
            'Y': [0],
            'Z': [0],
            'R': [0],
            'F': [0]
        })
        pt = Table(multipoint_frame, showtoolbar=False)
        pt.show()
        pt.model.df = df

