from tkinter import *
from tkinter import ttk

# Import Sub-Frames
from view.main_window_content.camera_display.tabs.camera_view_tab import camera_tab
from view.main_window_content.tabs.waveform_tab import waveform_tab

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


