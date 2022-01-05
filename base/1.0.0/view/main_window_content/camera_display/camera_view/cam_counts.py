from tkinter import *
from tkinter import ttk
from tkinter.font import Font


#Adds the contents of the camera selection/counts frame
class cam_counts(ttk.Frame):
    def __init__(self, cam_view, *args, **kwargs):
        ttk.Frame.__init__(self, cam_view, *args, **kwargs)

        # Creating Dropdown for camera select
        self.cam_num = StringVar()
        self.camera_pulldown = ttk.Combobox(self, textvariable=self.cam_num)
        self.camera_pulldown.state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        self.camera_pulldown.grid(row=0, column=0, sticky=(NSEW))

        #Max Counts Entry
        self.count = DoubleVar()
        self.count_entry_frame = ttk.Frame(self)
        self.count_entry = ttk.Entry(self.count_entry_frame, textvariable=self.count, width=15)
        self.count_entry_label = ttk.Label(self.count_entry_frame, text="Max Counts")
        self.count_entry_label.grid(row=0, column=0, sticky="s")
        self.count_entry.grid(row=1, column=0, sticky="n")
        self.count_entry_frame.grid(row=1, column=0, sticky=(NSEW))

        #Frames to Avg spinbox
        self.avg_frame = StringVar()
        self.avg_frame_holder = ttk.Frame(self)
        self.avg_frame_label = ttk.Label(self.avg_frame_holder, text="Frames to Avg")
        self.avg_frame_spinbox = ttk.Spinbox(self.avg_frame_holder, from_=0, to=500.0, textvariable=self.avg_frame,
            increment=1, width=9)
        self.avg_frame_label.grid(row=0, column=0, sticky=(NSEW))
        self.avg_frame_spinbox.grid(row=1, column=0, sticky=(NSEW))
        self.avg_frame_holder.grid(row=2, column=0, sticky=(NSEW))

        #Stack Max entry
        self.stack = DoubleVar()
        self.stack_frame = ttk.Frame(self)
        self.stack_entry = ttk.Entry(self.stack_frame, textvariable=self.stack, width=15)
        self.stack_entry_label = ttk.Label(self.stack_frame, text="Stack Max")
        self.stack_entry_label.grid(row=0, column=0, sticky="s")
        self.stack_entry.grid(row=1, column=0, sticky="n")
        self.stack_frame.grid(row=3, column=0, sticky=(NSEW))