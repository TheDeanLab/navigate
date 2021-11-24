from tkinter import *
from tkinter import ttk
import numpy as np


class settings_notebook(ttk.Notebook):
    def __init__(setntbk, frame_left, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(setntbk, frame_left, *args, **kwargs)
        #Putting notebook 1 into left frame
        setntbk.grid(row=0,column=0)
        #Creating the settings tab
        setntbk.settings_tab = settings_tab(setntbk)
        #Creating the advanced settings tab
        setntbk.adv_settings_tab = adv_settings_tab(setntbk)
        #Adding tabs to settings notebook
        setntbk.add(setntbk.settings_tab, text='Settings',sticky=NSEW)
        setntbk.add(setntbk.adv_settings_tab, text='Advanced Settings', sticky=NSEW)

class settings_tab(ttk.Frame):
    def __init__(settings, setntbk, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(settings, setntbk, *args, **kwargs)

        #Channel Settings
        #Gridding Major frames
        settings.channel_main = ttk.Labelframe(settings, text='Channel Settings')
        settings.channel_main.grid(row=0,column=0,sticky=(NSEW))
        settings.channels_label_frame = channels_label_frame(settings.channel_main)
        settings.channels_label_frame.grid_columnconfigure(0, weight=1) #Each of these is an attempt to get the labels lined up
        settings.channels_label_frame.grid_columnconfigure(1, weight=1)
        settings.channels_label_frame.grid_columnconfigure(2, weight=1)
        settings.channels_label_frame.grid_columnconfigure(3, weight=1)
        settings.channels_label_frame.grid_rowconfigure(0, weight=1)
        settings.channels_label_frame.grid(row=0,column=1, columnspan=3, sticky=(NSEW))
        settings.channel_1_frame = channel_frame(settings.channel_main, "1")
        settings.channel_1_frame.grid(row=1,column=0, columnspan=4, sticky=(NSEW))
        settings.channel_2_frame = channel_frame(settings.channel_main, "2")
        settings.channel_2_frame.grid(row=2,column=0, columnspan=4, sticky=(NSEW))
        settings.channel_3_frame = channel_frame(settings.channel_main, "3")
        settings.channel_3_frame.grid(row=3,column=0, columnspan=4, sticky=(NSEW))
        settings.channel_4_frame = channel_frame(settings.channel_main, "4")
        settings.channel_4_frame.grid(row=4,column=0, columnspan=4, sticky=(NSEW))
        settings.channel_5_frame = channel_frame(settings.channel_main, "5")
        settings.channel_5_frame.grid(row=5,column=0, columnspan=4, sticky=(NSEW))

        #Stack Acquisition Settings
        settings.stack_acq_frame = stack_acq_frame(settings)
        settings.stack_acq_frame.grid(row=6, column=0,columnspan=4,sticky=(NSEW), pady=10)


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
        chan_label_frame.exp_time_label = ttk.Label(chan_label_frame, text='Exposure Time in ms')
        chan_label_frame.exp_time_label.grid(row=0, column=2, sticky=(NSEW))
        
class channel_frame(ttk.Frame):
    def __init__(channel, settings_tab, num, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(channel, settings_tab, *args, **kwargs)

        #Creating checkbox
        on_off = StringVar()
        channel.chan_check = ttk.Checkbutton(
            channel,
            text='CH'+ num,
            variable=on_off
            #command=
            #onvalue=
            #offvalue=
            #state=
            #instate=
        )
        channel.chan_check.grid(row=0, column=0, sticky=(NSEW))

        #Creating Dropdowns

        #Laser
        channel.laser_options = StringVar()
        channel.laser_pull_down = ttk.Combobox(channel, textvariable=channel.laser_options)
        channel.laser_pull_down['values'] = ('a', 'f', 's', 'e')
        channel.laser_pull_down.state(["readonly"]) #Makes it so the user cannot type a choice into combobox
        channel.laser_pull_down.grid(row=0, column=1, sticky=(NSEW))

        #FilterWheel
        channel.filterwheel_options = StringVar()
        channel.filterwheel_pull_down = ttk.Combobox(channel, textvariable=channel.filterwheel_options)
        channel.filterwheel_pull_down['values'] = ('a', 'f', 's', 'e')
        channel.filterwheel_pull_down.state(["readonly"]) #Makes it so the user cannot type a choice into combobox
        channel.filterwheel_pull_down.grid(row=0, column=2, sticky=(NSEW))
        
        #Exposure Time spinbox
        channel.exp_time_spinval = StringVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        channel.exp_time_spinbox = ttk.Spinbox(
            channel,
            from_=0, 
            to=5000.0, 
            textvariable=channel.exp_time_spinval, #this holds the data in the entry
            increment=25, 
            width=9
            #TODO command= function from connector
        )
        channel.exp_time_spinbox.grid(row=0, column=3, sticky=(NSEW))

class stack_acq_frame(ttk.Labelframe):
    def __init__(stack_acq, settings_tab, *args, **kwargs):

        #Init Frame
        ttk.Labelframe.__init__(stack_acq, settings_tab, text='Stack Aquisition Settings', *args, **kwargs)

        #Step Size Frame (Vertically oriented)
        stack_acq.step_size_frame = ttk.Frame(stack_acq)
        stack_acq.step_size_label = ttk.Label(stack_acq.step_size_frame, text='Step Size')
        stack_acq.step_size_label.grid(row=0, column=0, sticky=(S))
        stack_acq.step_size_spinval = StringVar()
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




'''
End of Settings Tab Classes
'''



class adv_settings_tab(ttk.Frame):
    def __init__(adv_settings, setntbk, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(adv_settings, setntbk, *args, **kwargs)
