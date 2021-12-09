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
import concurrency.concurrency_tools as ct
from view.main_application_window import Main_App as ASLM_view
from model.aslm_model import session as ASLM_model

class ASLM_controller():
    def __init__(self, root):
        self.model = ASLM_model()
        self.model.addCallback(self.model)

        self.view1 = ASLM_view(root)

    def model_changed(self):


        ####### Connect buttons / variables from GUI with functions here-----------------------------------
        # connect all the buttons that start a functionality like preview, stack acquisition, etc.
        # connect all the buttons that you want to dynamically change, e.g. during preview
        # don't connect buttons that you want to be "static" during a stack acquisition, such as number of planes, plane spacing
        # those parameters, you can get at the beginning of e.g. a stack acquisition call

        self.view.frame_left.settings_notebook.channels_tab.stack_cycling_frame.cycling_pull_down.bind("<<ComboboxSelected>>", self.update_cycling_pull_down)



if __name__ == '__main__':
    # Testing section.

    print("done")





