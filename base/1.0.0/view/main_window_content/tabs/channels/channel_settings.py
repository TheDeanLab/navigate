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
        channel.exp_time_spinbox = ttk.Spinbox(channel, from_=0, to=5000.0, textvariable=channel.exp_time_spinval,
            increment=25, width=9)
        channel.exp_time_spinbox.grid(row=0, column=3, sticky=(NSEW))

class channel_checkboxes(ttk.Frame):
    def __init__(self, channels_tab, num, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, channels_tab, *args, **kwargs)

        self.channel_variables = []
        self.channel_checks = []
        for num in range(5):
            self.channel_variables[num] = BooleanVar()
            self.channel_checks[num] = ttk.Checkbutton(self, text='CH' + (num+1), variable=self.channel_variables[num])
            self.channel_checks[num].grid(row=num, column=0, sticky=(NSEW))

class laser_drops(ttk.Frame):
    def __init__(self, channels_tab, num, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, channels_tab, *args, **kwargs)

        #Laser Label
        self.laser_label = ttk.Label(self, text='Laser')
        self.laser_label.grid(row=0, column=0, sticky=(NSEW))

        #Drops
        self.laser_variables = []
        self.laser_pulldowns = []
        for num in range(5):
            self.laser_variables[num] = StringVar()
            self.laser_pulldowns[num] = ttk.Combobox(self, textvariable=self.laser_variables[num])
            self.laser_pulldowns[num].grid(row=num, column=0, sticky=(NSEW))

class laserpower(ttk.Frame):
    def __init__(self, channels_tab, num, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, channels_tab, *args, **kwargs)

        #Laser Label
        self.laserpower_label = ttk.Label(self, text='Laser Power')
        self.laserpower_label.grid(row=0, column=0, sticky=(NSEW))

        #Drops
        self.laserpower_variables = []
        self.laserpower_pulldowns = []
        for num in range(5):
            self.laserpower_variables[num] = StringVar()
            self.laserpower_pulldowns[num] = ttk.Combobox(self, textvariable=self.laserpower_variables[num])
            self.laserpower_pulldowns[num].grid(row=num, column=0, sticky=(NSEW))

class filterwheel_drops(ttk.Frame):
    def __init__(self, channels_tab, num, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, channels_tab, *args, **kwargs)

        #Filterwheel Label
        self.filterwheel_label = ttk.Label(self, text='Filterwheel')
        self.filterwheel_label.grid(row=0, column=0, sticky=(NSEW))

        #Drops
        self.filterwheel_variables = []
        self.filterwheel_pulldowns = []
        for num in range(5):
            self.filterwheel_variables[num] = StringVar()
            self.filterwheel_pulldowns[num] = ttk.Combobox(self, textvariable=self.filterwheel_variables[num])
            self.filterwheel_pulldowns[num].grid(row=num, column=0, sticky=(NSEW))

class exposuretime_drops(ttk.Frame):
    def __init__(self, channels_tab, num, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, channels_tab, *args, **kwargs)

        #Exposure Time Label
        self.exptime_label = ttk.Label(self, text='Exposure Time (ms)')
        self.exptime_label.grid(row=0, column=0, sticky=(NSEW))

        #Drops
        self.exptime_variables = []
        self.exptime_pulldowns = []
        for num in range(5):
            self.exptime_variables[num] = StringVar()
            self.exptime_pulldowns[num] = ttk.Combobox(self, textvariable=self.exptime_variables[num])
            self.exptime_pulldowns[num].grid(row=num, column=0, sticky=(NSEW))

class interval_spins(ttk.Frame):
    def __init__(self, channels_tab, num, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, channels_tab, *args, **kwargs)

        #Time Interval Label
        self.interval_label = ttk.Label(self, text='Time Interval (ms)')
        self.interval_label.grid(row=0, column=0, sticky=(NSEW))

        #Spins
        self.interval_variables = []
        self.interval_pulldowns = []
        for num in range(5):
            self.interval_variables[num] = StringVar()
            self.interval_pulldowns[num] = ttk.Combobox(self, textvariable=self.interval_variables[num])
            self.interval_pulldowns[num].grid(row=num, column=0, sticky=(NSEW))