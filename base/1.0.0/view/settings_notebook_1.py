from tkinter import *
from tkinter import ttk
from tkinter.font import Font

import numpy as np


class settings_notebook(ttk.Notebook):
    def __init__(setntbk, frame_left, session, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(setntbk, frame_left, *args, **kwargs)

        #Putting notebook 1 into left frame
        setntbk.grid(row=0,column=0)

        #Creating the settings tab
        setntbk.settings_tab = settings_tab(setntbk, session)

        #Creating the advanced settings tab
        setntbk.adv_settings_tab = adv_settings_tab(setntbk)

        #Adding tabs to settings notebook
        setntbk.add(setntbk.settings_tab, text='Settings', sticky=NSEW)
        setntbk.add(setntbk.adv_settings_tab, text='Advanced Settings', sticky=NSEW)

class settings_tab(ttk.Frame):
    def __init__(settings, setntbk, session, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(settings, setntbk, *args, **kwargs)

        #Channel Settings
        #Gridding Major frames
        settings.channel_main = ttk.Labelframe(settings, text='Channel Settings')
        settings.channel_main.grid(row=0, column=0, sticky=(NSEW))
        settings.channels_label_frame = channels_label_frame(settings.channel_main)

        #Each of these is an attempt to get the labels lined up
        settings.channels_label_frame.grid_columnconfigure(0, weight=1)
        settings.channels_label_frame.grid_columnconfigure(1, weight=1)
        settings.channels_label_frame.grid_columnconfigure(2, weight=1)
        settings.channels_label_frame.grid_columnconfigure(3, weight=1)
        settings.channels_label_frame.grid_rowconfigure(0, weight=1)
        settings.channels_label_frame.grid(row=0,column=1, columnspan=3, sticky=(NSEW))

        settings.channel_1_frame = channel_frame(settings.channel_main, "1", session)
        settings.channel_1_frame.grid(row=1,column=0, columnspan=4, sticky=(NSEW))

        settings.channel_2_frame = channel_frame(settings.channel_main, "2", session)
        settings.channel_2_frame.grid(row=2,column=0, columnspan=4, sticky=(NSEW))

        settings.channel_3_frame = channel_frame(settings.channel_main, "3", session)
        settings.channel_3_frame.grid(row=3,column=0, columnspan=4, sticky=(NSEW))

        settings.channel_4_frame = channel_frame(settings.channel_main, "4", session)
        settings.channel_4_frame.grid(row=4,column=0, columnspan=4, sticky=(NSEW))

        settings.channel_5_frame = channel_frame(settings.channel_main, "5", session)
        settings.channel_5_frame.grid(row=5,column=0, columnspan=4, sticky=(NSEW))

        #Stack Acquisition Settings
        settings.stack_acq_frame = stack_acq_frame(settings)
        settings.stack_acq_frame.grid(row=5, column=0, columnspan=5, sticky=(NSEW), pady=10)

        #Stack Cycling Settings
        settings.stack_cycling_frame = stack_cycling_frame(settings)
        settings.stack_cycling_frame.grid(row=6, column=0, columnspan=5, sticky=(NSEW), pady=10)

'''
Settings Tab Classes
'''

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
            variable=on_off
            #command=
            #onvalue=
            #offvalue=
            #state=
            #instate=
        )
        channel.chan_check.grid(row=0, column=0, sticky=(NSEW))

        # Creating Dropdowns
        # Lasers - Gets values from the configuration file and populates pulldown.
        number_of_lasers = session.AcquisitionHardware['number_of_lasers']
        laser_list = []
        for i in range(number_of_lasers):
            laser_wavelength = session.AcquisitionHardware['laser_'+str(i)+'_wavelength']
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

class stack_acq_frame(ttk.Labelframe):
    def __init__(stack_acq, settings_tab, *args, **kwargs):

        #Init Frame
        text_label = 'Stack Acquisition Settings (' + "\N{GREEK SMALL LETTER MU}" + 'm)'
        ttk.Labelframe.__init__(stack_acq, settings_tab, text=text_label, *args, **kwargs)

        #Step Size Frame (Vertically oriented)
        stack_acq.step_size_frame = ttk.Frame(stack_acq)
        stack_acq.step_size_label = ttk.Label(stack_acq.step_size_frame, text='Step Size')
        stack_acq.step_size_label.grid(row=0, column=0, sticky=(S))


        stack_acq.step_size_spinval = StringVar()
        # Set default step size to 160nm
        if stack_acq.step_size_spinval.get() == '':
            stack_acq.step_size_spinval.set('0.160')
        stack_acq.step_size_spinbox = ttk.Spinbox(
            stack_acq.step_size_frame,
            from_=0, 
            to=500.0, 
            textvariable=stack_acq.step_size_spinval, #this holds the data in the entry
            increment=0.5, 
            width=14
            #TODO command= function from connector
        )
        stack_acq.step_size_spinbox.grid(row=1, column=0, sticky=(N))

        #Start Pos Frame (Vertically oriented)
        stack_acq.start_pos_frame = ttk.Frame(stack_acq)
        stack_acq.start_pos_label = ttk.Label(stack_acq.start_pos_frame, text='Start Pos')
        stack_acq.start_pos_label.grid(row=0, column=0, sticky=(S))
        stack_acq.start_pos_spinval = StringVar()
        # set default start value to 0 nm
        if stack_acq.start_pos_spinval.get() == '':
            stack_acq.start_pos_spinval.set('0')
        stack_acq.start_pos_spinbox = ttk.Spinbox(
            stack_acq.start_pos_frame,
            from_=0, 
            to=500.0, 
            textvariable=stack_acq.start_pos_spinval, #this holds the data in the entry
            increment=0.5, 
            width=14
            #TODO command= function from connector
        )
        stack_acq.start_pos_spinbox.grid(row=1, column=0, sticky=(N))

        #End Pos Frame (Vertically oriented)
        stack_acq.end_pos_frame = ttk.Frame(stack_acq)
        stack_acq.end_pos_label = ttk.Label(stack_acq.end_pos_frame, text='End Pos')
        stack_acq.end_pos_label.grid(row=0, column=0, sticky=(S))
        stack_acq.end_pos_spinval = StringVar()
        # Set default end position to 200 microns
        if stack_acq.end_pos_spinval.get() == '':
            stack_acq.end_pos_spinval.set('200')
        stack_acq.end_pos_spinbox = ttk.Spinbox(
            stack_acq.end_pos_frame,
            from_=0, 
            to=500.0, 
            textvariable=stack_acq.end_pos_spinval, #this holds the data in the entry
            increment=0.5, 
            width=14
            #TODO command= function from connector
        )
        stack_acq.end_pos_spinbox.state(['disabled']) #Starts it disabled
        stack_acq.end_pos_spinbox.grid(row=1, column=0, sticky=(N))

        #Slice Frame (Vertically oriented)
        stack_acq.slice_frame = ttk.Frame(stack_acq)
        stack_acq.slice_label = ttk.Label(stack_acq.slice_frame, text='Slice')
        stack_acq.slice_label.grid(row=0, column=0, sticky=(S))
        stack_acq.slice_spinval = StringVar() #Attempts to get slice value with
        stack_acq.slice_spinbox = ttk.Spinbox(
            stack_acq.slice_frame,
            from_=0, 
            to=500.0, 
            textvariable=stack_acq.slice_spinval, #this holds the data in the entry
            increment=0.5, 
            width=14
            #TODO command= function from connector
        )
        stack_acq.slice_spinbox.state(['disabled']) #Starts it disabled
        stack_acq.slice_spinbox.grid(row=1, column=0, sticky=(N))

        #Gridding Each Holder Frame
        stack_acq.step_size_frame.grid(row=0, column=0, sticky=(NSEW))
        stack_acq.start_pos_frame.grid(row=0, column=1, sticky=(NSEW))
        stack_acq.end_pos_frame.grid(row=0, column=2, sticky=(NSEW))
        stack_acq.slice_frame.grid(row=0, column=3, sticky=(NSEW))

class stack_cycling_frame(ttk.Labelframe):
    def __init__(stack_acq, settings_tab, *args, **kwargs):

        #Init Frame
        text_label = 'Laser Cycling Settings'
        ttk.Labelframe.__init__(stack_acq, settings_tab, text=text_label, *args, **kwargs)

        #Laser Cycling Frame (Vertically oriented)
        stack_acq.cycling_frame = ttk.Frame(stack_acq)
        stack_acq.cycling_options = StringVar()
        stack_acq.cycling_pull_down = ttk.Combobox(stack_acq, textvariable=stack_acq.cycling_options)
        stack_acq.cycling_pull_down['values'] = ['Per Z', 'Per Stack']
        stack_acq.cycling_pull_down.current(0)
        stack_acq.cycling_pull_down.state(["readonly"]) # Makes it so the user cannot type a choice into combobox
        stack_acq.cycling_pull_down.grid(row=0, column=1, sticky=(NSEW))

        #Gridding Each Holder Frame
        stack_acq.cycling_frame.grid(row=0, column=0, sticky=(NSEW))


'''
End of Settings Tab Classes
'''



class adv_settings_tab(ttk.Frame):
    def __init__(adv_settings, setntbk, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(adv_settings, setntbk, *args, **kwargs)
