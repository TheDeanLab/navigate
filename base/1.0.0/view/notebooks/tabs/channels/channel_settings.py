from tkinter import *
from tkinter import ttk
import numpy as np

class channels_label_frame(ttk.Frame):
    def __init__(chan_label_frame, settings_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(chan_label_frame, settings_tab, *args, **kwargs)

        #Adding Labels to frame
        #Laser Label
        chan_label_frame.laser_label = ttk.Label(chan_label_frame, text='Laser')
        chan_label_frame.laser_label.grid(row=0, column=0, sticky=(NSEW))

        #FilterWheel Label
        chan_label_frame.filterwheel_label = ttk.Label(chan_label_frame, text='Filterwheel')
        chan_label_frame.filterwheel_label.grid(row=0, column=1, sticky=(NSEW))

        #Exposure Time Label
        chan_label_frame.exp_time_label = ttk.Label(chan_label_frame, text='Exposure Time (ms)')
        chan_label_frame.exp_time_label.grid(row=0, column=2, sticky=(NSEW))

class channel_frame(ttk.Frame):
    def __init__(channel, settings_tab, num, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(channel, settings_tab, *args, **kwargs)

        #Creating checkbox
        #on_off = StringVar()
        channel.on_off = BooleanVar()
        channel.chan_check = ttk.Checkbutton(channel, text='CH' + num, variable=channel.on_off)
        channel.chan_check.grid(row=0, column=0, sticky=(NSEW))

        # Creating Dropdowns
        channel.laser_options = StringVar()
        channel.laser_pull_down = ttk.Combobox(channel, textvariable=channel.laser_options)
        channel.laser_pull_down.state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        channel.laser_pull_down.grid(row=0, column=1, sticky=(NSEW))

        channel.filterwheel_options = StringVar()
        channel.filterwheel_pull_down = ttk.Combobox(channel, textvariable=channel.filterwheel_options)
        channel.filterwheel_pull_down.state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        channel.filterwheel_pull_down.grid(row=0, column=2, sticky=(NSEW))

        # Exposure Time spinbox
        # Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        channel.exp_time_spinval = StringVar()
        # Set default exposure time in milliseconds
        if channel.exp_time_spinval == '':
            channel.exp_time_spinval.set('200')
        channel.exp_time_spinbox = ttk.Spinbox(
            channel,
            from_=0,
            to=5000.0,
            textvariable=channel.exp_time_spinval,
            increment=25,
            width=9
        )
        channel.exp_time_spinbox.grid(row=0, column=3, sticky=(NSEW))
