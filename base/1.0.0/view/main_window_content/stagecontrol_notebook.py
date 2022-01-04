# Standard Imports
from tkinter import *
from tkinter import ttk
from tkinter.font import Font

# Local Imports
from view.main_window_content.tabs.stage_control_tab import stage_control_tab
from view.main_window_content.tabs.stage_control.maximum_intensity_projection_tab import maximum_intensity_projection_tab

class stagecontrol_maxintensity_notebook(ttk.Notebook):
    def __init__(stagecontrol_maxintensity, frame_bot_right, *args, **kwargs):

        #Init notebook
        ttk.Notebook.__init__(stagecontrol_maxintensity, frame_bot_right, *args, **kwargs)

        #Putting notebook 3 into bottom right frame
        stagecontrol_maxintensity.grid(row=0, column=0)

        #Creating Stage Control Tab
        stagecontrol_maxintensity.stage_control_tab = stage_control_tab(stagecontrol_maxintensity)

        #Creating Max intensity projection Tab
        stagecontrol_maxintensity.maximum_intensity_projection_tab = maximum_intensity_projection_tab(stagecontrol_maxintensity)

        #Adding tabs to stagecontrol_maxintensity notebook
        stagecontrol_maxintensity.add(stagecontrol_maxintensity.stage_control_tab, text='Stage Control', sticky=NSEW)
        stagecontrol_maxintensity.add(stagecontrol_maxintensity.maximum_intensity_projection_tab, text='MIPs', sticky=NSEW)


class goto_frame(ttk.Frame):
    def __init__(goto_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(goto_frame, stage_control_tab, *args, **kwargs) 

'''
End of Stage Control Tab Frame Classes
'''