from tkinter import *
from tkinter import ttk
#import camera_view_for_tab as controller

class camera_waveform_notebook(ttk.Notebook):
    def __init__(cam_wave, frame_top_right, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(cam_wave, frame_top_right, *args, **kwargs)
        #Putting notebook 2 into top right frame
        cam_wave.grid(row=0,column=0)
        #Creating the camera tab
        cam_wave.camera_tab = camera_tab(cam_wave)
        #Creating the waveform settings tab
        cam_wave.waveform_tab = waveform_tab(cam_wave)
        #Adding tabs to cam_wave notebook
        cam_wave.add(cam_wave.camera_tab, text='Camera View',sticky=NSEW)
        cam_wave.add(cam_wave.waveform_tab, text='Waveform Settings', sticky=NSEW)

class camera_tab(ttk.Frame):
   def __init__(camera_tab, cam_wave, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(camera_tab, cam_wave, *args, **kwargs) 
        #Need to add image code here, using a label to hold the image.
        #image_viewer = ttk.Label(camera_tab)
        #image_viewer.grid(row=0, column=0, sticky=NSEW) 

class waveform_tab(ttk.Frame):
   def __init__(waveform_tab, cam_wave, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(waveform_tab, cam_wave, *args, **kwargs) 