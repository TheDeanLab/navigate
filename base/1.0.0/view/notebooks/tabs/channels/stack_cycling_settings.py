from tkinter import *
from tkinter import ttk
from tkinter.font import Font
import numpy as np

class stack_cycling_frame(ttk.Labelframe):
    def __init__(stack_acq, settings_tab, session, verbose, *args, **kwargs):

        #Init Frame
        text_label = 'Laser Cycling Settings'
        ttk.Labelframe.__init__(stack_acq, settings_tab, text=text_label, *args, **kwargs)

        #Laser Cycling Frame (Vertically oriented)
        stack_acq.cycling_frame = ttk.Frame(stack_acq)
        stack_acq.cycling_options = StringVar()
        stack_acq.cycling_pull_down = ttk.Combobox(stack_acq, textvariable=stack_acq.cycling_options)
        stack_acq.cycling_pull_down['values'] = ['Per Z', 'Per Stack']
        stack_acq.cycling_pull_down.current(0)
        stack_acq.cycling_pull_down.state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        stack_acq.cycling_pull_down.grid(row=0, column=1, sticky=(NSEW))

        #Gridding Each Holder Frame
        stack_acq.cycling_frame.grid(row=0, column=0, sticky=(NSEW))

        # Signal changes to the pull down menu
        def save_to_session(stack_acq, session, verbose):
            stack_cycling_state = stack_acq.cycling_pull_down.get()
            if stack_cycling_state == 'Per Z':
                session.MicroscopeState['stack_cycling_state'] = 'Per_Z'
            elif stack_cycling_state == 'Per Stack':
                session.MicroscopeState['stack_cycling_state'] = 'Per_Stack'
            session.MicroscopeState['stack_cycling'] = stack_acq.cycling_pull_down.get()
            if verbose:
                print("The Microscope State is now:", session.MicroscopeState['stack_cycling'])

        #stack_acq.cycling_pull_down.bind('<<ComboboxSelected>>', lambda event: save_to_session(stack_acq, session, verbose))
