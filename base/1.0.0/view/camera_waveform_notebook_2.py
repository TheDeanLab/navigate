from tkinter import *
from tkinter import ttk
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

from model.daq import waveforms as waveforms
from model.camera.synthetic_camera import Camera as camera

#import camera_view_for_tab as controller

class camera_waveform_notebook(ttk.Notebook):
    def __init__(cam_wave, frame_top_right, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(cam_wave, frame_top_right, *args, **kwargs)

        #Putting notebook 2 into top right frame
        cam_wave.grid(row=0, column=0)

        #Creating the camera tab
        cam_wave.camera_tab = camera_tab(cam_wave)

        #Creating the waveform settings tab
        cam_wave.waveform_tab = waveform_tab(cam_wave)

        #Adding tabs to cam_wave notebook
        cam_wave.add(cam_wave.camera_tab, text='Camera View', sticky=NSEW)
        cam_wave.add(cam_wave.waveform_tab, text='Waveform Settings', sticky=NSEW)

class camera_tab(ttk.Frame):
   def __init__(camera_tab, cam_wave, *args, **kwargs):
       #TODO: WOuld like to split this Frame in half and provide some statistics on the right-hand side.
       # Would include a Combobox for changing the CMAP.
       # Would include a Spinbox for providing the maximum intensity of the image.
       # Would include a Spinbox for providing a rolling average maximum intensity of the image
       # Would include a Spinbox for providing the number of frames to include in the rolling average.
        #Init Frame
        ttk.Frame.__init__(camera_tab, cam_wave, *args, **kwargs)

        # the figure that will contain the plot
        fig = Figure(figsize=(4, 4), dpi=100)

        # Generate Waveform
        synthetic_image = camera.read_camera(camera)

        # adding the subplot
        plot1 = fig.add_subplot(111)
        plot1.axis('off')

        # add the image
        #TODO: Handle the synthetic and real images.
        plot1.imshow(synthetic_image, cmap='gray')

        # creating the Tkinter canvas containing the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=camera_tab)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

        #Need to add image code here, using a label to hold the image.
        #image_viewer = ttk.Label(camera_tab)
        #image_viewer.grid(row=0, column=0, sticky=NSEW) 

class waveform_tab(ttk.Frame):
    def __init__(waveform_tab, cam_wave, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(waveform_tab, cam_wave, *args, **kwargs)

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
        canvas = FigureCanvasTkAgg(fig, master=waveform_tab)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()


        # placing the toolbar on the Tkinter window
        #canvas.get_tk_widget().pack()

    #plot(waveform_tab)