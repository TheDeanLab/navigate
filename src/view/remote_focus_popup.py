from tkinter import *
import tkinter as tk
from tkinter import ttk
from view.custom_widgets.popup import PopUp
from view.custom_widgets.LabelInputWidgetFactory import LabelInput



class remote_popup():
    '''
    #### Class creates the popup that is generated when the Acquire button is pressed and Save File checkbox is selected.
    '''
    def __init__(self, root, *args, **kwargs):
        
        # Creating popup window with this name and size/placement, PopUp is a Toplevel window
        self.popup = PopUp(root, "Remote Focus Settings", '1200x800+320+180', transient=False)

        # Storing the content frame of the popup, this will be the parent of the widgets
        content_frame = self.popup.get_frame()

        '''Creating the widgets for the popup'''
        #Dictionary for all the variables
        self.inputs = {}
        self.buttons = {}

