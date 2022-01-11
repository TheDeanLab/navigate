from tkinter import *
from tkinter import ttk
from tkinter.font import Font
import numpy as np


class stack_acq_frame(ttk.Labelframe):
    def __init__(stack_acq, settings_tab, *args, **kwargs):

        #Init Frame
        text_label = 'Stack Acquisition Settings (' + "\N{GREEK SMALL LETTER MU}" + 'm)'
        ttk.Labelframe.__init__(stack_acq, settings_tab, text=text_label, *args, **kwargs)

        #Step Size Frame (Vertically oriented)
        stack_acq.step_size_frame = ttk.Frame(stack_acq)
        stack_acq.step_size_label = ttk.Label(stack_acq.step_size_frame, text='Step Size')
        stack_acq.step_size_label.grid(row=0, column=0, sticky=(S))
        stack_acq.step_size_spinval = StringVar()
        # Set default step size to 160nm
        if stack_acq.step_size_spinval.get() == '':
            stack_acq.step_size_spinval.set('0.160')
        stack_acq.step_size_spinbox = ttk.Spinbox(
            stack_acq.step_size_frame,
            from_=0,
            to=500.0,
            textvariable=stack_acq.step_size_spinval,
            increment=0.5,
            width=14
        )
        stack_acq.step_size_spinbox.grid(row=1, column=0, sticky=(N))

    #Start Pos Frame (Vertically oriented)
        stack_acq.start_pos_frame = ttk.Frame(stack_acq)
        stack_acq.start_pos_label = ttk.Label(stack_acq.start_pos_frame, text='Start Pos')
        stack_acq.start_pos_label.grid(row=0, column=0, sticky=(S))
        stack_acq.start_pos_spinval = StringVar()
        # set default start value to 0 nm
        if stack_acq.start_pos_spinval.get() == '':
            stack_acq.start_pos_spinval.set('0')
        stack_acq.start_pos_spinbox = ttk.Spinbox(
            stack_acq.start_pos_frame,
            from_=0,
            to=500.0,
            textvariable=stack_acq.start_pos_spinval,
            increment=0.5,
            width=14
        )
        stack_acq.start_pos_spinbox.grid(row=1, column=0, sticky=(N))


    #End Pos Frame (Vertically oriented)
        stack_acq.end_pos_frame = ttk.Frame(stack_acq)
        stack_acq.end_pos_label = ttk.Label(stack_acq.end_pos_frame, text='End Pos')
        stack_acq.end_pos_label.grid(row=0, column=0, sticky=(S))
        stack_acq.end_pos_spinval = StringVar()
        # Set default end position to 200 microns
        if stack_acq.end_pos_spinval.get() == '':
            stack_acq.end_pos_spinval.set('200')
        stack_acq.end_pos_spinbox = ttk.Spinbox(
            stack_acq.end_pos_frame,
            from_=0,
            to=500.0,
            textvariable=stack_acq.end_pos_spinval,
            increment=0.5,
            width=14
        )
        stack_acq.end_pos_spinbox.grid(row=1, column=0, sticky=(N))

    #Slice Frame (Vertically oriented)
        stack_acq.slice_frame = ttk.Frame(stack_acq)
        stack_acq.slice_label = ttk.Label(stack_acq.slice_frame, text='Slice')
        stack_acq.slice_label.grid(row=0, column=0, sticky=(S))
        stack_acq.slice_spinval = StringVar()
        stack_acq.slice_spinval.set(int(1))
        stack_acq.slice_spinval.set(np.int(1250))
        stack_acq.slice_spinbox = ttk.Spinbox(
            stack_acq.slice_frame,
            from_=0,
            to=500.0,
            textvariable=stack_acq.slice_spinval,
            increment=0.5,
            width=14
        )
        stack_acq.slice_spinbox.state(['disabled'])
        stack_acq.slice_spinbox.grid(row=1, column=0, sticky=(N))

        #Gridding Each Holder Frame
        stack_acq.step_size_frame.grid(row=0, column=0, sticky=(NSEW))
        stack_acq.start_pos_frame.grid(row=0, column=1, sticky=(NSEW))
        stack_acq.end_pos_frame.grid(row=0, column=2, sticky=(NSEW))
        stack_acq.slice_frame.grid(row=0, column=3, sticky=(NSEW))


