"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model (./model/aslm_model.py).
Use: https://www.python-course.eu/tkinter_events_binds.php
"""

# Import Standard Python Packages
import time
from threading import Thread
import numpy as np
import datetime as dt
import os
import glob

# Import GUI Packages
import tkinter as tk
from tkinter import ttk

# Import Local Packages
# import concurrency.concurrency_tools as ct
from view.main_application_window import Main_App as ASLM_view
from model import session as ASLM_model

class ASLM_controller():
    def __init__(self, root):
        self.model = ASLM_model()
        self.model.addCallback(self.model)
        self.view = ASLM_view(root)

        ####### Connect buttons / variables from GUI with functions here-----------------------------------
        # connect all the buttons that start a functionality like preview, stack acquisition, etc.
        # connect all the buttons that you want to dynamically change, e.g. during preview
        # don't connect buttons that you want to be "static" during a stack acquisition, such as number of planes, plane spacing
        # those parameters, you can get at the beginning of e.g. a stack acquisition call

        #self.view.frame_left.settings_notebook.channels_tab.stack_cycling_frame.cycling_pull_down.bind("<<ComboboxSelected>>", self.update_cycling_pull_down)
        #self.view.frame_left.settings_notebook.channels_tab.stack_cycling_frame.cycling_pull_down.bind('<<ComboboxSelected>>', lambda event: save_to_session(stack_acq, session, verbose))

        # Stack_Settings
        # If the step size is changed (default = 0.16), the number of slices is recalculated
        self.view.frame_left.settings_notebook.channels_tab.stack_acq_frame.step_size_spinval.trace_add('write', lambda *args: calculate_number_of_z_steps())

        # If the start position is changed (default = 0), the number of slices is recalculated
        self.view.frame_left.settings_notebook.channels_tab.stack_acq_frame.start_pos_spinval.trace_add('write', lambda *args: calculate_number_of_z_steps())

        # If the end position is changed (default = 200), the number of slices is recalculated
        self.view.frame_left.settings_notebook.channels_tab.stack_acq_frame.end_pos_spinval.trace_add('write', lambda *args: calculate_number_of_z_steps())

    def calculate_number_of_z_steps(self):
        print("We are trying to calculate the number of z steps!")
        #Calculate number of steps
        start_position = np.float(self.view.frame_left.settings_notebook.channels_tab.stack_acq_frame.start_pos_spinval.get())
        end_position = np.float(self.view.frame_left.settings_notebook.channels_tab.stack_acq_frame.end_pos_spinval.get())
        step_size = np.float(self.view.frame_left.settings_notebook.channels_tab.stack_acq_frame.step_size_spinval.get())
        number_of_steps = np.floor((end_position - start_position)/step_size)

        # Save Values to Session
        session.MicroscopeState['step_size'] = step_size
        session.MicroscopeState['start_position'] = start_position
        session.MicroscopeState['end_position'] = end_position

        # Update GUI
        self.view.frame_left.settings_notebook.channels_tab.stack_acq_frame.slice_spinval.set(number_of_steps)


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



if __name__ == '__main__':
    # Testing section.

    print("done")





