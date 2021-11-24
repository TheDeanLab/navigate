'''
This class will be imported to control the acquisition bar frame. Any events that the acquistiion bar 
causes will be handled here. Both listening for events and then handling. Once the model is established 
then anything that needs to be actioned on that side of the architechture will go thru this module to the view
'''

'''
https://sukhbinder.wordpress.com/2014/12/25/an-example-of-model-view-controller-design-pattern-with-tkinter-python/
Will need to rebuild a controller base class that has children of all the pieces,
this way can continue to pass things down and give the controlling class easier access
to the buttons it needs etc. It will look similar to the View class but has the bindings and functions
to process the bindings
'''
from tkinter import *
import tkinter as tk
from tkinter import ttk
from view.acquire_bar_frame.acquire_bar import AcquireBar as AcqBar
from view.settings_notebook_1 import stack_acq_frame

#Pass this the frame that is being controlled in this case acquire bar from 
class acqbar_controller():
    def __init__(acq_cont, AcqBar,*args, **kwargs):

        #Function to handle events
        def zstack():
            pass

        #Triggers virtual event when the acquire type drop down changes value
        AcqBar.pull_down.bind('<<ComboboxSelected>>', zstack)