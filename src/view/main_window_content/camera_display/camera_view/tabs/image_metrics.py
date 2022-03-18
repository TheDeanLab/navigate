#Adds the contents of the camera selection/counts frame
from tkinter import *
from tkinter import ttk
import tkinter as tk

from view.custom_widgets.LabelInputWidgetFactory import LabelInput


class image_metrics(ttk.Labelframe):
    def __init__(self, cam_view, *args, **kwargs):
        # Init Labelframe
        text_label = 'Image Metrics'
        ttk.Labelframe.__init__(self, cam_view, text=text_label, *args, **kwargs)
        
        # Dictionary for widgets
        self.inputs = {}

        # Labels and names
        self.labels = ['Frames to Avg', 'Image Max Counts', 'Channel']
        self.names = ['Frames', 'Image', 'Channel']

        # Loop for widgets
        for i in range(len(self.labels)):
            if i == 0:
                self.inputs[self.names[i]] = LabelInput(parent=self,
                                                        label=self.labels[i],
                                                        input_class=ttk.Spinbox,
                                                        input_var=IntVar(),
                                                        input_args={'from_':1, 'to':20, 'increment':1, 'width':9}
                                                        )
                self.inputs[self.names[i]].grid(row=0, column=i, sticky=(NSEW))
            if i > 0:
                self.inputs[self.names[i]] = LabelInput(parent=self,
                                                        label=self.labels[i],
                                                        input_class=ttk.Entry,
                                                        input_var=IntVar(),
                                                        input_args={'width':15}
                                                        )
                self.inputs[self.names[i]].grid(row=0, column=i, sticky=(NSEW))

    def get_variables(self):
        '''
        # This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
        '''
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get()
        return variables
    
    def get_widgets(self):
        '''
        # This function returns the dictionary that holds the widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        '''
        return self.inputs

        #Stack Max entry
        # self.stack = DoubleVar()
        # self.stack_frame = ttk.Frame(self)
        # self.stack_entry = ttk.Entry(self.stack_frame, textvariable=self.stack, width=15)
        # self.stack_entry_label = ttk.Label(self.stack_frame, text="Stack Max")
        # self.stack_entry_label.grid(row=0, column=0, sticky="s")
        # self.stack_entry.grid(row=0, column=1, sticky="n")
        # self.stack_frame.grid(row=0, column=1, sticky=NSEW)
