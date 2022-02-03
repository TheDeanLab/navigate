import tkinter as tk
from tkinter import *
from tkinter import ttk


class channel_creator(ttk.LabelFrame):
    def __init__(self, channels_tab, *args, **kwargs):

        #  Init Frame
        self.title = 'Channel Settings'
        ttk.LabelFrame.__init__(self, channels_tab, text=self.title, *args, **kwargs)

        #  Arrays with Widget Variables and widgets themselves
        #  TODO refactor using dicts for variables and one for widgets,
        #   allow access to arrays via a key. might be overly complicated.
        #   Below way is clear just a bit repetitive
        #  Channel Checkbuttons
        self.channel_variables = []
        self.channel_checks = []

        #  Laser Dropdowns
        self.laser_variables = []
        self.laser_pulldowns = []

        #  LaserPower Dropdowns
        self.laserpower_variables = []
        self.laserpower_pulldowns = []

        #  FilterWheel Dropdowns
        self.filterwheel_variables = []
        self.filterwheel_pulldowns = []

        #  Exposure Time Dropdowns
        self.exptime_variables = []
        self.exptime_pulldowns = []

        #  Time Interval Spinboxes
        self.interval_variables = []
        self.interval_spins = []

        #  Channel Creation

        #  Grids labels them across the top row of each column
        self.label_text = ["Channel", "Laser", "Laser Power", "Filter", "Exp. Time (ms)", "Interval"]
        self.labels = []
        self.frame_columns = []

        #  Creates a column frame for each widget, this is to help with the lables lining up
        for idx in range(len(self.label_text)):
            self.frame_columns.append(ttk.Frame(self))
            self.frame_columns[idx].grid(row=0, column=idx, sticky=NSEW)
            self.labels.append(ttk.Label(self.frame_columns[idx], text=self.label_text[idx]))
            self.labels[idx].grid(row=0, column=0, sticky=N, pady=1, padx=1)
            
        
        #  Adds and grids widgets to respective column
        #  TODO add connection to config file to specify the range.
        #   This will allow custom selection of amount of channels.
        #   Also may need further refactoring
        for num in range(0, 5):
            #  This will add a widget to each column frame for the respecitive types
            #  Channel Checkboxes
            self.channel_variables.append(BooleanVar())
            self.channel_checks.append(ttk.Checkbutton(self.frame_columns[0], text='CH' + str(num+1),
                                                       variable=self.channel_variables[num]))
            self.channel_checks[num].grid(row=num+1, column=0, sticky=NSEW, padx=1)

            #  Laser Dropdowns
            self.laser_variables.append(StringVar())
            self.laser_pulldowns.append(ttk.Combobox(self.frame_columns[1],
                                                     textvariable=self.laser_variables[num], width=8))
            self.laser_pulldowns[num].state(["readonly"])
            self.laser_pulldowns[num].grid(row=num+1, column=0, sticky=NSEW, padx=1)

            #  Laser Power Spinbox
            self.laserpower_variables.append(StringVar())
            self.laserpower_pulldowns.append(ttk.Spinbox(self.frame_columns[2], style='My.TSpinbox', from_=0, to=100.0,
                                                         textvariable=self.laserpower_variables[num],
                                                         increment=25, width=8))
            self.laserpower_pulldowns[num].grid(row=num+1, column=0, sticky=NSEW, padx=1)

            #  FilterWheel Dropdowns
            self.filterwheel_variables.append(StringVar())
            self.filterwheel_pulldowns.append(ttk.Combobox(self.frame_columns[3],
                                                           textvariable=self.filterwheel_variables[num], width=8))
            self.filterwheel_pulldowns[num].state(["readonly"])
            self.filterwheel_pulldowns[num].grid(row=num+1, column=0, sticky=NSEW, padx=1)

            #  Exposure Time Spinboxes
            self.exptime_variables.append(StringVar())
            self.exptime_pulldowns.append(ttk.Spinbox(self.frame_columns[4], from_=0, to=5000.0,
                                                      textvariable=self.exptime_variables[num], increment=25, width=8))
            self.exptime_pulldowns[num].grid(row=num+1, column=0, sticky=NSEW, padx=1)

            #  Time Interval Spinboxes
            self.interval_variables.append(StringVar())
            self.interval_spins.append(ttk.Spinbox(self.frame_columns[5], from_=0, to=5000.0,
                                                   textvariable=self.interval_variables[num], increment=5, width=8))
            self.interval_spins[num].grid(row=num+1, column=0, sticky=NSEW, padx=1)


if __name__ == '__main__':
    root = tk.Tk()
    channel_creator(root).grid(row=0, column=0, sticky=NSEW)
    root.mainloop()