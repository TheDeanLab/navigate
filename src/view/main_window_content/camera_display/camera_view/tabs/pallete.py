from tkinter import *
from tkinter import ttk

from pyparsing import col

from view.custom_widgets.LabelInputWidgetFactory import LabelInput


class pallete(ttk.Labelframe):
    def __init__(self, cam_view, *args, **kwargs):
        #Init Frame
        text_label = 'Lookup Table'
        ttk.Labelframe.__init__(self, cam_view, text=text_label, *args, **kwargs)

        # Dictionary for widgets
        self.inputs = {}
        

        # Labels and names
        self.color_labels = ['Gray', 'Gradient', 'Rainbow']
        self.color_values = ['gray', 'hot', 'viridis']
        self.color = StringVar()
        self.autoscale = BooleanVar()
        self.auto = 'Autoscale'
        self.minmax = ['Min Counts', 'Max Counts']
        self.minmax_names = ['Min', 'Max']


        # Radiobuttons - Gray is default
        for i in range(len(self.color_labels)):
            self.inputs[self.color_labels[i]] = LabelInput(parent=self,
                                                    label=self.color_labels[i],
                                                    input_class=ttk.Radiobutton,
                                                    input_var=self.color,
                                                    input_args={'value':self.color_values[i]}
                                                    )
            self.inputs[self.color_labels[i]].grid(row=i, column=0, sticky=(NSEW))                                         
        
        
        #  Autoscale checkbox - Invoked by default.
        # self.autoscale = BooleanVar()
        # self.inputs['Autoscale'] = ttk.Checkbutton(self,
        #                                        text="Autoscale",
        #                                        variable=self.autoscale)
        # self.inputs['Autoscale'].grid(row=3, column=0, sticky=NSEW)
        self.inputs[self.auto] = LabelInput(parent=self,
                                                    label=self.auto,
                                                    input_class=ttk.Checkbutton,
                                                    input_var=self.autoscale
                                                    )
        self.inputs[self.auto].grid(row=3, column=0, sticky=(NSEW)) 

        # Max and Min Counts
        for i in range(len(self.minmax)):
            self.inputs[self.minmax_names[i]] = LabelInput(parent=self,
                                                    label=self.minmax[i],
                                                    input_class=ttk.Spinbox,
                                                    input_var=IntVar(),
                                                    input_args={'from_':1,'to':65000,'increment':1,'width':5}
                                                    )
            self.inputs[self.minmax_names[i]].grid(row=i+4, column=0, sticky=(NSEW))

        
    def get_variables(self):
        '''
        # This function returns a dictionary of all the variables that are tied to each widget name.
        The key is the widget name, value is the variable associated.
        '''
        variables = {}
        for key, widget in self.inputs.items():
            variables[key] = widget.get()
        return variables
    
    def get_widgets(self):
        '''
        # This function returns the dictionary that holds the widgets.
        The key is the widget name, value is the LabelInput class that has all the data.
        '''
        return self.inputs



