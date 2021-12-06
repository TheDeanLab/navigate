from tkinter import *
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os

#Handles populating the window with entries etc
class popup_entries(ttk.Frame):

    def __init__(content, popup, toplevel, session, *args, **kwargs):
        #Init content with frame attr
        ttk.Frame.__init__(content, popup, *args, **kwargs)
        frame_width = 25

        #Setting up entries and Done/Cancel button

        #Label for entries
        content.entries_label = ttk.Label(content, text="Please fill out the fields below")

        #Root Save Path - Provided by configuration file
        content.root_entry_frame = ttk.Frame(content)
        content.root_entry = ttk.Entry(content.root_entry_frame, width=frame_width)
        content.root_entry_label = ttk.Label(content.root_entry_frame, text="Root Directory")
        content.root_entry_label.grid(row=0, column=0, sticky="e")
        content.root_entry.grid(row=0, column=1, sticky="w")
        content.root_entry.insert(END, session.Saving['root_directory'])

        #User Entry
        content.user_entry_frame = ttk.Frame(content)
        content.user_string = tk.StringVar()
        content.user_entry = ttk.Entry(content.user_entry_frame, textvariable=content.user_string, width=frame_width)
        content.user_entry_label = ttk.Label(content.user_entry_frame, text="User")
        content.user_entry_label.grid(row=0, column=0, sticky="e")
        content.user_entry.grid(row=0, column=1, sticky="w")
        if session.Saving['user'] is not None:
            content.user_entry.insert(END, session.Saving['user'])

        #Tissue Entry
        content.tissue_entry_frame = ttk.Frame(content)
        content.tissue_string = tk.StringVar()
        content.tissue_entry = ttk.Entry(content.tissue_entry_frame, textvariable=content.tissue_string, width=frame_width)
        content.tissue_entry_label = ttk.Label(content.tissue_entry_frame, text="Tissue Type")
        content.tissue_entry_label.grid(row=0, column=0, sticky="e")
        content.tissue_entry.grid(row=0, column=1, sticky="w")
        if session.Saving['tissue'] is not None:
            content.tissue_entry.insert(END, session.Saving['tissue'])

        #Cell Type Entry
        content.celltype_entry_frame = ttk.Frame(content)
        content.celltype_string = tk.StringVar()
        content.celltype_entry = ttk.Entry(content.celltype_entry_frame, textvariable=content.celltype_string, width=frame_width)
        content.celltype_entry_label = ttk.Label(content.celltype_entry_frame, text="Cell Type")
        content.celltype_entry_label.grid(row=0, column=0, sticky="e")
        content.celltype_entry.grid(row=0, column=1, sticky="w")
        if session.Saving['celltype'] is not None:
            content.celltype_entry.insert(END, session.Saving['celltype'])

        #Label Entry
        content.label_entry_frame = ttk.Frame(content)
        content.label_string = tk.StringVar()
        content.label_entry = ttk.Entry(content.label_entry_frame, textvariable=content.label_string, width=frame_width)
        content.label_entry_label = ttk.Label(content.label_entry_frame, text="Label")
        content.label_entry_label.grid(row=0, column=0, sticky="e")
        content.label_entry.grid(row=0, column=1, sticky="w")
        if session.Saving['label'] is not None:
            content.label_entry.insert(END, session.Saving['label'])

        #Misc. Information to be saved into the metadata.
        content.meta_entry_frame = ttk.Frame(content)
        content.meta_entry = ttk.Entry(content.meta_entry_frame, width=frame_width)
        content.meta_entry_label = ttk.Label(content.meta_entry_frame, text="Misc. Information:")
        content.meta_entry_label.grid(row=0, column=0, sticky="e")
        content.meta_entry.grid(row=0, column=1, sticky="w")

        # Need to create the save path, and update the model from the entries.
        def parse_entries():
            # Parse the Variables
            user_string = content.user_string.get()
            if len(user_string) == 0:
                raise ValueError('Please provide a User Name')

            tissue_string = content.tissue_string.get()
            if len(tissue_string) == 0:
                raise ValueError('Please provide a Tissue Type')

            celltype_string = content.celltype_string.get()
            if len(celltype_string) == 0:
                raise ValueError('Please provide a Cell Type')

            label_string = content.label_string.get()
            if len(label_string) == 0:
                raise ValueError('Please provide a Label Type')

            date_string = str(datetime.now().date())

            # Make sure that there are no spaces in the variables
            user_string = user_string.replace(" ", "-")
            tissue_string = tissue_string.replace(" ", "-")
            celltype_string = celltype_string.replace(" ", "-")
            label_string = label_string.replace(" ", "-")

            # Specify Saving Directory
            save_directory = os.path.join(session.Saving['root_directory'], user_string, tissue_string, celltype_string, label_string, date_string)

            if not os.path.exists(save_directory):
                os.makedirs(save_directory)

            # Determine Number of Cells in Directory
            cell_index = 0
            cell_string = "Cell-" + str(cell_index).zfill(6)
            while os.path.exists(os.path.join(save_directory, cell_string)):
                    cell_index += 1

            save_directory = os.path.join(session.Saving['root_directory'], user_string, tissue_string, celltype_string, label_string, date_string, cell_string)
            print("Data Saved to:", save_directory)

            # Update the Model
            session.Saving = {
                'save_directory': save_directory,
                'user': user_string,
                'tissue': tissue_string,
                'celltype': celltype_string,
                'label': label_string,
                'date': date_string
            }

            #TODO: Begin the acquisition

            # Close the window
            toplevel.dismiss()

        # Done and Cancel Buttons
        # Will call the Acquire_Popup class dismiss function toplevel is acqPop above
        # Will need more code to use inputs to generate path for directory

        content.done_btn = ttk.Button(content, text="Acquire Data", command=parse_entries)
        content.cancel_btn = ttk.Button(content, text="Cancel Acquisition", command=toplevel.dismiss)

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

        content.entries_label.grid(row=0, column=0, columnspan=2, sticky=(NSEW))
        content.root_entry_frame.grid(row=1, column=0, columnspan=2, sticky=(NSEW))
        content.user_entry_frame.grid(row=2, column=0, columnspan=2, sticky=(NSEW))
        content.tissue_entry_frame.grid(row=3, column=0, columnspan=2, sticky=(NSEW))
        content.celltype_entry_frame.grid(row=4, column=0, columnspan=2, sticky=(NSEW))
        content.label_entry_frame.grid(row=5, column=0, columnspan=2, sticky=(NSEW))
        content.meta_entry_frame.grid(row=6, column=0, columnspan=2, sticky=(NSEW))
        content.cancel_btn.grid(row=7, column=0, sticky=(NSEW))
        content.done_btn.grid(row=7, column=1, sticky=(NSEW))