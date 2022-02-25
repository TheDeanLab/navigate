from tkinter import *
from tkinter import ttk
import tkinter as tk

from view.custom_widgets.LabelInputWidgetFactory import LabelInput


class pallete(ttk.Labelframe):
    def __init__(self, cam_view, *args, **kwargs):
        ttk.Frame.__init__(self, cam_view, *args, **kwargs)

        #Init Frame
        text_label = 'Lookup Table'
        ttk.Labelframe.__init__(self, cam_view, text=text_label, *args, **kwargs)

        self.pallete = ttk.Frame(self)
        self.pallete.grid(row=0, column=0, sticky=(NSEW))

        # #Holds dropdowns, this is done in case more widgets are to be added in a different frame, these can be grouped together
        # content_frame = ttk.Frame(self)
        # content_frame.grid(row=0, column=0, sticky=(NSEW))
        

        # #Dictionary for all the variables, this will be used by the controller
        # self.inputs = {}
        # self.labels = ['Gray', 'Gradient', 'Rainbow', 'Autoscale', 'Min. Counts', 'Max. Counts']
        # self.names = ['Gray', 'Gradient', 'Rainbow', 'Autoscale', 'Min', 'Max']
        # self.color = StringVar()

        # # Radio buttons
        # for i in range(len(self.labels)):
        #     self.inputs[self.names[i]] = LabelInput(parent=content_frame,
        #                                                 label=self.labels[i],
        #                                                 input_class=ttk.Radiobutton,
        #                                                 input_var=self.color                                          
        #                                                 )
        #     self.inputs[self.names[i]].grid(row=i, column=0, pady=1)


        #  Radiobuttons for pallete - Gray set by default.
        self.color = StringVar()
        self.gray = ttk.Radiobutton(self.pallete,
                                    text="Gray",
                                    variable=self.color,
                                    value='gray')

        self.gradient = ttk.Radiobutton(self.pallete,
                                        text="Gradient",
                                        variable=self.color,
                                        value='hot')

        self.rainbow = ttk.Radiobutton(self.pallete,
                                       text="Rainbow",
                                       variable=self.color,
                                       value='viridis')
        self.gray.invoke()
        self.gray.grid(row=0, column=0, sticky=NSEW)
        self.gradient.grid(row=1, column=0, sticky=NSEW)
        self.rainbow.grid(row=2, column=0, sticky=NSEW)

        #  Autoscale checkbox - Invoked by default.
        self.autoscale = BooleanVar()
        self.autoscale_check = ttk.Checkbutton(self,
                                               text="Autoscale",
                                               variable=self.autoscale)
        self.autoscale_check.invoke()
        self.autoscale_check.grid(row=1, column=0, sticky=NSEW)

        #  Minimum Counts
        self.min_counts = IntVar()
        self.min_counts.set(110)
        self.min_counts_holder = ttk.Frame(self)
        self.min_counts_label = ttk.Label(self.min_counts_holder,
                                          text="Min. Counts")
        self.min_counts_spinbox = ttk.Spinbox(self.min_counts_holder,
                                              from_=1,
                                              to=65000,
                                              textvariable=self.min_counts,
                                              increment=1,
                                              width=5,
                                              state=NORMAL)
        self.min_counts_label.grid(row=3, column=0, sticky=NSEW)
        self.min_counts_spinbox.grid(row=3, column=1, sticky=NSEW)
        self.min_counts_holder.grid(row=3, column=0, sticky=NSEW)

        #  Maximum Counts
        self.max_counts = IntVar()
        self.max_counts.set(5000)
        self.max_counts_holder = ttk.Frame(self)
        self.max_counts_label = ttk.Label(self.max_counts_holder,
                                          text="Max. Counts")
        self.max_counts_spinbox = ttk.Spinbox(self.max_counts_holder,
                                              from_=1,
                                              to=65000,
                                              textvariable=self.max_counts,
                                              increment=1,
                                              width=5,
                                              state=NORMAL)
        self.max_counts_label.grid(row=4, column=0, sticky=NSEW)
        self.max_counts_spinbox.grid(row=4, column=1, sticky=NSEW)
        self.max_counts_holder.grid(row=4, column=0, sticky=NSEW)




