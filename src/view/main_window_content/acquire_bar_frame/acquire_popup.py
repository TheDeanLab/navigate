from cProfile import label
from tkinter import *
import tkinter as tk
from tkinter import ttk
from view.custom_widgets.popup import PopUp
from view.custom_widgets.LabelInputWidgetFactory import LabelInput
from .popup_entries import popup_entries

#Class that handles the dialog box that has all the user entry stuff when you press the Acquisition button
class Acquire_PopUp():
    '''
    #### Class creates the popup that is generated when the Acquire button is pressed and Save File checkbox is selected.
    '''
    def __init__(self, root, *args, **kwargs):
        
        # Creating popup window with this name and size/placement, PopUp is a Toplevel window
        self.popup = PopUp(root, "File Saving Dialog", '600x400+320+180', transient=True)

        # Storing the content frame of the popup, this will be the parent of the widgets
        content_frame = self.popup.get_frame()

        '''Creating the widgets for the popup'''
        #Dictionary for all the variables
        self.inputs = {}
        self.buttons = {}

        #Label for entries
        self.entries_label = ttk.Label(content_frame, text="Please fill out the fields below")
        self.entries_label.grid(row=0, column=0, columnspan=2, sticky=(NSEW))

        # Creating Entry Widgets
        entry_names = ['Root', 'User', 'Tissue', 'Cell', 'Label', 'Misc']
        entry_labels = ['Root Directory', 'User', 'Tissue Type', 'Cell Type', 'Label', 'Misc. Info']

        # Loop for each entry and label
        for i in range(len(entry_names)):
            self.inputs[entry_names[i]] = LabelInput(parent=content_frame,
                                         label=entry_labels[i],
                                         input_class=ttk.Entry,
                                         input_var=StringVar()                                        
                                        )
            self.inputs[entry_names[i]].grid(row=i+1, column=0, columnspan=2,sticky=(NSEW))

        #Done and Cancel Buttons
        self.buttons['Cancel'] = ttk.Button(content_frame, text="Cancel Acquisition")
        self.buttons['Cancel'].grid(row=7, column=0, sticky=(NSEW))
        self.buttons['Done'] = ttk.Button(content_frame, text="Acquire Data")
        self.buttons['Done'].grid(row=7, column=1, sticky=(NSEW))
        

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
        # This function returns the dictionary that holds the input widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        '''
        return self.inputs

    def get_buttons(self):
        '''
        # This function returns the dictionary that holds the buttons.
        The key is the button name, value is the button.
        '''
        return self.buttons
        