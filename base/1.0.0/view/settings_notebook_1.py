from tkinter import *
from tkinter import ttk


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

        #Pulldown menu for laser
        settings.laser_pulldown_frame = ttk.Frame(settings)
        settings.laser_options = StringVar()
        settings.laser_pull_down = ttk.Combobox(settings.laser_pulldown_frame, textvariable=settings.laser_options)
        settings.laser_pull_down['values'] = ('a', 'f', 's', 'e')
        settings.laser_pull_down.state(["readonly"]) #Makes it so the user cannot type a choice into combobox
        settings.laser_pulldown_label = ttk.Label(settings.laser_pulldown_frame, text="Laser")
        settings.laser_pulldown_label.grid(row=0, column=0, sticky="e")
        settings.laser_pull_down.grid(row=0, column=1, sticky="w")

        #Pulldown menu for filter wheel
        settings.filterwheel_pulldown_frame = ttk.Frame(settings)
        settings.filterwheel_options = StringVar()
        settings.filterwheel_pull_down = ttk.Combobox(settings.filterwheel_pulldown_frame, textvariable=settings.filterwheel_options)
        settings.filterwheel_pull_down['values'] = ('a', 'f', 's', 'e')
        settings.filterwheel_pull_down.state(["readonly"]) #Makes it so the user cannot type a choice into combobox
        settings.filterwheel_pulldown_label = ttk.Label(settings.filterwheel_pulldown_frame, text="Filterwheel")
        settings.filterwheel_pulldown_label.grid(row=0, column=0, sticky="e")
        settings.filterwheel_pull_down.grid(row=0, column=1, sticky="w")

        #Spinbox for exposure time
        settings.exp_time_spinbox_frame = ttk.Frame(settings)
        settings.exp_time_spinval = StringVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        settings.exp_time_spinbox = ttk.Spinbox(
            settings.exp_time_spinbox_frame, 
            from_=0, 
            to=5000.0, 
            textvariable=settings.exp_time_spinval, #this holds the data in the entry
            increment=25, 
            width=9
            #TODO command= function from connector
        )
        settings.exp_time_spinbox_label = ttk.Label(settings.exp_time_spinbox_frame, text='Exposure\nTime\nin ms')
        settings.exp_time_spinbox_label.grid(row=0, column=0, sticky="e")
        settings.exp_time_spinbox.grid(row=0, column=1, sticky='w')
        

        #Gridding out frames for each piece
        settings.laser_pulldown_frame.grid(row=0,column=0,sticky=(NSEW))
        settings.filterwheel_pulldown_frame.grid(row=1,column=0,sticky=(NSEW))
        settings.exp_time_spinbox_frame.grid(row=2,column=0,sticky=(NSEW))




class adv_settings_tab(ttk.Frame):
    def __init__(adv_settings, setntbk, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(adv_settings, setntbk, *args, **kwargs)
