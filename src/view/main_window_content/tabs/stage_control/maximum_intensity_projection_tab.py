# Standard Imports
from tkinter import ttk
from tkinter import *
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class maximum_intensity_projection_tab(ttk.Frame):
    def __init__(self, note3, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(self, note3, *args, **kwargs)

        # Generate MIPs
        def xy_mip():
            pass

        def xz_mip():
            pass

        def yz_mip():
            pass

        # the figure that will contain the plot
        fig = Figure(figsize=(11, 3), tight_layout=True)

        #  Data to just fill void
        t = np.arange(0.0, 2.0, 0.01)
        s1 = np.sin(2*np.pi*t)
        s2 = np.sin(4*np.pi*t)

        # adding the subplot
        plot1 = fig.add_subplot(131)
        plot1.plot(t, s1)
        fig.gca().set_axis_off()

        plot2 = fig.add_subplot(132)
        plot2.plot(t, s2)
        fig.gca().set_axis_off()

        plot3 = fig.add_subplot(133)
        plot3.plot(t, s2*2)
        fig.gca().set_axis_off()

        # creating the Tkinter canvas
        # containing the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()

        # placing the canvas on the Tkinter window
        # canvas.get_tk_widget().pack()
        canvas.get_tk_widget().grid(row=0, column=0, sticky=NSEW)

        self.calculate_button = ttk.Button(self, text="Calculate MIPs")
        self.calculate_button.grid(row=1, column=0, sticky=NSEW)