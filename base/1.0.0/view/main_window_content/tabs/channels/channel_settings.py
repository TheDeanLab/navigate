import tkinter as tk
from tkinter import *
from tkinter import ttk
import numpy as np

class channel_creator(ttk.Frame):
    def __init__(self, channels_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(self, channels_tab, *args, **kwargs)

        #Arrays with Widget Variables and widgets themselves
        #TODO refactor using dicts for variables and one for widgets, allow access to arrays via a key. might be overly complicated. Below way is clear just a bit repetitive
        #Channel Checkbuttons
        self.channel_variables = []
        self.channel_checks = []
        #Laser Dropdowns
        self.laser_variables = []
        self.laser_pulldowns = []
        #LaserPower Dropdowns
        self.laserpower_variables = []
        self.laserpower_pulldowns = []
        #FilterWheel Dropdowns
        self.filterwheel_variables = []
        self.filterwheel_pulldowns = []
        #Exposure Time Dropdowns
        self.exptime_variables = []
        self.exptime_pulldowns = []
        #Time Interval Spinboxes
        self.interval_variables = []
        self.interval_spins = []

        #Label Creation for each larger widget ie all the laser dropdowns, all the filterwheel dropdowns etc
        #Grids them across the top row
        #TODO create a custom class or function that will make "title" frames so that a label can be associated with a column of widgets
        labels = ["Channel Select", "Laser", "Laser Power", "Filterwheel", "Exposure Time (ms)", "Time Interval (ms)"]
        self.labels_frame = ttk.Frame(self)
        self.labels_frame.grid(row=0,column=0,sticky=(NSEW))
        #Junky way to format stuff, will need to find more elegant solution
        for idx in range(len(labels)):
            if idx == 0: #To make sure the first label stays put
                ttk.Label(self.labels_frame, text=labels[idx]).grid(row=0, column=idx, sticky=(W))
            else:
                if idx == 5: #To bring the last label back to the left
                    ttk.Label(self.labels_frame, text=labels[idx]).grid(row=0, column=idx, sticky=(W))
                else:
                    ttk.Label(self.labels_frame, text=labels[idx]).grid(row=0, column=idx, sticky=(NSEW), padx=45)
            
        
            

        #Channel Creation
        self.channels = []
        #TODO add connection to config file to specify the range. This will allow custom selection of amount of channels. Also may need further refactoring
        for num in range(0, 5):
            
            #This will create a frame for each channel and then grid each widget into this new frame, each channel frame will be grid into this larger class widget

            #Creating Channel Frame for ease of use
            self.channels.append(ttk.Frame(self))
            self.channels[num].grid(row=num+1, column=0, sticky=(NSEW))

            #Channel Checkboxes
            self.channel_variables.append(BooleanVar())
            self.channel_checks.append(ttk.Checkbutton(self.channels[num], text='CH' + str(num+1), variable=self.channel_variables[num]))
            self.channel_checks[num].grid(row=0, column=0, sticky=(NSEW), padx=13)

            #Laser Dropdowns
            self.laser_variables.append(StringVar())
            self.laser_pulldowns.append(ttk.Combobox(self.channels[num], textvariable=self.laser_variables[num]))
            self.laser_pulldowns[num].state(["readonly"]) # Makes it so the user cannot type a choice into combobox
            self.laser_pulldowns[num].grid(row=0, column=1, sticky=(NSEW), padx=10)

            #Laser Power Dropdowns
            self.laserpower_variables.append(StringVar())
            self.laserpower_pulldowns.append(ttk.Combobox(self.channels[num], textvariable=self.laserpower_variables[num]))
            self.laserpower_pulldowns[num].state(["readonly"]) # Makes it so the user cannot type a choice into combobox
            self.laserpower_pulldowns[num].grid(row=0, column=2, sticky=(NSEW), padx=10)

            #FilterWheel Dropdowns
            self.filterwheel_variables.append(StringVar())
            self.filterwheel_pulldowns.append(ttk.Combobox(self.channels[num], textvariable=self.filterwheel_variables[num]))
            self.filterwheel_pulldowns[num].state(["readonly"]) # Makes it so the user cannot type a choice into combobox
            self.filterwheel_pulldowns[num].grid(row=0, column=3, sticky=(NSEW), padx=13)

            #Exposure Time Spinboxes
            self.exptime_variables.append(StringVar())
            self.exptime_pulldowns.append(ttk.Spinbox(self.channels[num],from_=0, to=5000.0, textvariable=self.exptime_variables[num], increment=25, width=9))
            self.exptime_pulldowns[num].grid(row=0, column=4, sticky=(NSEW), padx=13)

            #Time Interval Spinboxes
            self.interval_variables.append(StringVar())
            self.interval_spins.append(ttk.Spinbox(self.channels[num],from_=0, to=5000.0, textvariable=self.interval_variables[num], increment=5, width=9))
            self.interval_spins[num].grid(row=0, column=5, sticky=(NSEW), padx=10)

    #def default_settings():


if __name__ == '__main__':
    root = tk.Tk()
    channel_creator(root).grid(row=0, column=0,sticky=(NSEW))
    root.mainloop()