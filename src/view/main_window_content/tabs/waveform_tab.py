from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)

from model import aslm_model_waveforms as waveforms


#.devices.daq import waveforms as waveforms

class waveform_tab(ttk.Frame):
    def __init__(self, cam_wave, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(self, cam_wave, *args, **kwargs)
        #TODO: Update waveforms according to the current model?
        #TODO: How do you detect changes to the model to rerun the code?
        #TODO: Convert waveforms so that they can take different exposure times.
        #TODO: Concatenate each channel into a consecutive waveform as the microscope actually will.

        # the figure that will contain the plot
        fig = Figure(figsize=(8, 4), dpi=100)

        # Generate Waveform
        remote_focus_waveform = waveforms.smooth_waveform(waveforms.tunable_lens_ramp(), 10)
        laser_waveform = waveforms.square()
        trigger_waveform = waveforms.single_pulse()

        # adding the subplot
        plot1 = fig.add_subplot(111)

        # plotting the graph
        plot1.plot(remote_focus_waveform, label='Remote Focus')
        plot1.plot(laser_waveform, label='Laser')
        plot1.plot(trigger_waveform, label='Ext. Trigger')
        plot1.legend(loc='upper right')

        # creating the Tkinter canvas
        # containing the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()


        # placing the toolbar on the Tkinter window
        #canvas.get_tk_widget().pack()

    #plot(self)