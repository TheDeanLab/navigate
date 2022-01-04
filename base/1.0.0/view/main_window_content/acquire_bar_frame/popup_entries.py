from tkinter import *
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os

#Handles populating the window with entries etc
class popup_entries(ttk.Frame):

    def __init__(self, popup, toplevel, *args, **kwargs):
        #Init self with frame attr
        ttk.Frame.__init__(self, popup, *args, **kwargs)
        frame_width = 25

        #Setting up entries and Done/Cancel button

        #Label for entries
        self.entries_label = ttk.Label(self, text="Please fill out the fields below")

        #Root Save Path - Provided by configuration file
        self.root_entry_frame = ttk.Frame(self)
        self.root_entry_string = StringVar()
        self.root_entry = ttk.Entry(self.root_entry_frame, textvariable=self.root_entry_string, width=frame_width)
        self.root_entry_label = ttk.Label(self.root_entry_frame, text="Root Directory")
        self.root_entry_label.grid(row=0, column=0, sticky="e")
        self.root_entry.grid(row=0, column=1, sticky="w")

        #User Entry
        self.user_entry_frame = ttk.Frame(self)
        self.user_string = tk.StringVar()
        self.user_entry = ttk.Entry(self.user_entry_frame, textvariable=self.user_string, width=frame_width)
        self.user_entry_label = ttk.Label(self.user_entry_frame, text="User")
        self.user_entry_label.grid(row=0, column=0, sticky="e")
        self.user_entry.grid(row=0, column=1, sticky="w")

        #Tissue Entry
        self.tissue_entry_frame = ttk.Frame(self)
        self.tissue_string = tk.StringVar()
        self.tissue_entry = ttk.Entry(self.tissue_entry_frame, textvariable=self.tissue_string, width=frame_width)
        self.tissue_entry_label = ttk.Label(self.tissue_entry_frame, text="Tissue Type")
        self.tissue_entry_label.grid(row=0, column=0, sticky="e")
        self.tissue_entry.grid(row=0, column=1, sticky="w")

        #Cell Type Entry
        self.celltype_entry_frame = ttk.Frame(self)
        self.celltype_string = tk.StringVar()
        self.celltype_entry = ttk.Entry(self.celltype_entry_frame, textvariable=self.celltype_string, width=frame_width)
        self.celltype_entry_label = ttk.Label(self.celltype_entry_frame, text="Cell Type")
        self.celltype_entry_label.grid(row=0, column=0, sticky="e")
        self.celltype_entry.grid(row=0, column=1, sticky="w")

        #Label Entry
        self.label_entry_frame = ttk.Frame(self)
        self.label_string = tk.StringVar()
        self.label_entry = ttk.Entry(self.label_entry_frame, textvariable=self.label_string, width=frame_width)
        self.label_entry_label = ttk.Label(self.label_entry_frame, text="Label")
        self.label_entry_label.grid(row=0, column=0, sticky="e")
        self.label_entry.grid(row=0, column=1, sticky="w")

        #Misc. Information to be saved into the metadata.
        self.meta_entry_frame = ttk.Frame(self)
        self.meta_entry = ttk.Entry(self.meta_entry_frame, width=frame_width)
        self.meta_entry_label = ttk.Label(self.meta_entry_frame, text="Misc. Information:")
        self.meta_entry_label.grid(row=0, column=0, sticky="e")
        self.meta_entry.grid(row=0, column=1, sticky="w")

        # Done and Cancel Buttons
        # Will call the Acquire_Popup class dismiss function toplevel is acqPop above
        # Will need more code to use inputs to generate path for directory

        self.done_btn = ttk.Button(self, text="Acquire Data")
        self.cancel_btn = ttk.Button(self, text="Cancel Acquisition")

        #Assign a lambda to the button command, passing whatever you want into that function.
        #command=lambda: whatever(pass_your_data_from_entry)

        #Gridding out entries and buttons
        '''
        Grid for buttons

                00  01
                02  03
                04  05 
                06  07
                08  09
                10  11
                12  13

        Entries Label is 00,01
        User Entry is 02,03
        Tissue is 04,05
        Cell Type is 06,07
        Label is 08,09
        Cell Number is 10,11
        Cancel btn is 12
        Done btn is 13
        '''

        self.entries_label.grid(row=0, column=0, columnspan=2, sticky=(NSEW))
        self.root_entry_frame.grid(row=1, column=0, columnspan=2, sticky=(NSEW))
        self.user_entry_frame.grid(row=2, column=0, columnspan=2, sticky=(NSEW))
        self.tissue_entry_frame.grid(row=3, column=0, columnspan=2, sticky=(NSEW))
        self.celltype_entry_frame.grid(row=4, column=0, columnspan=2, sticky=(NSEW))
        self.label_entry_frame.grid(row=5, column=0, columnspan=2, sticky=(NSEW))
        self.meta_entry_frame.grid(row=6, column=0, columnspan=2, sticky=(NSEW))
        self.cancel_btn.grid(row=7, column=0, sticky=(NSEW))
        self.done_btn.grid(row=7, column=1, sticky=(NSEW))