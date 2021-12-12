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
    def __init__(channel, settings_tab, num, session, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(channel, settings_tab, *args, **kwargs)

        #Creating checkbox
        on_off = StringVar()
        channel.chan_check = ttk.Checkbutton(
            channel,
            text='CH' + num,
            variable=on_off)
        channel.chan_check.grid(row=0, column=0, sticky=(NSEW))

        # Creating Dropdowns
        # Lasers - Gets values from the configuration file and populates pulldown.
        number_of_lasers = np.int(session.DAQParameters['number_of_lasers'])
        laser_list = []
        for i in range(number_of_lasers):
            laser_wavelength = session.DAQParameters['laser_'+str(i)+'_wavelength']
            laser_list.append(laser_wavelength)
        channel.laser_options = StringVar()
        channel.laser_pull_down = ttk.Combobox(channel, textvariable=channel.laser_options)
        channel.laser_pull_down['values'] = laser_list
        channel.laser_pull_down.state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        channel.laser_pull_down.grid(row=0, column=1, sticky=(NSEW))
        #TODO: Have it save the parameters to session.

        # FilterWheel - Gets values from the configuration file and populates pulldown.
        filter_dictionary = session.FilterWheelParameters['available_filters']
        channel.filterwheel_options = StringVar()
        channel.filterwheel_pull_down = ttk.Combobox(channel, textvariable=channel.filterwheel_options)
        channel.filterwheel_pull_down['values'] = list(filter_dictionary.keys())
        channel.filterwheel_pull_down.state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        channel.filterwheel_pull_down.grid(row=0, column=2, sticky=(NSEW))
        #TODO: Have it save the parameters to session.

        # Exposure Time spinbox
        # Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        channel.exp_time_spinval = StringVar()
        # Set default exposure time in milliseconds
        if channel.exp_time_spinval.get() == '':
            channel.exp_time_spinval.set('200')
        channel.exp_time_spinbox = ttk.Spinbox(
            channel,
            from_=0,
            to=5000.0,
            textvariable=channel.exp_time_spinval, #this holds the data in the entry
            increment=25,
            width=9
            #TODO command= function from connector.  Also, have it save parameters to session.
        )
        channel.exp_time_spinbox.grid(row=0, column=3, sticky=(NSEW))
