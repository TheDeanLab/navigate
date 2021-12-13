from tkinter import *
import tkinter as tk
from tkinter import ttk
from .popup_entries import popup_entries

#Class that handles the dialog box that has all the user entry stuff when you press the Acquisition button
class Acquire_PopUp():

    def __init__(acqPop, root, *args, **kwargs):
        #This starts the popup window config, and makes sure that any child widgets can be resized with the window
        acqPop.toplevel_acquire_popup = tk.Toplevel()
        acqPop.toplevel_acquire_popup.title("File Saving Dialog")
        acqPop.toplevel_acquire_popup.geometry('600x400+320+180') #300x200 pixels, first +320 means 320 pixels from left edge, +180 means 180 pixels from top edge
        acqPop.toplevel_acquire_popup.columnconfigure(0, weight=1)
        acqPop.toplevel_acquire_popup.rowconfigure(0, weight=1)
        acqPop.toplevel_acquire_popup.resizable(FALSE, FALSE) #Makes it so user cannot resize
        acqPop.toplevel_acquire_popup.attributes("-topmost", 1) #Makes it be on top of mainapp when called
        
        acqPop.toplevel_acquire_popup.protocol("WM_DELETE_WINDOW", acqPop.dismiss) #Intercepting close button
        acqPop.toplevel_acquire_popup.transient(root) #Prevents clicking outside of window
        acqPop.toplevel_acquire_popup.wait_visibility() # Can't grab until window appears, so we wait
        acqPop.toplevel_acquire_popup.grab_set()   #Ensures any input goes to this window

        #Putting popup frame into toplevel window
        acqPop.popup_frame = ttk.Frame(acqPop.toplevel_acquire_popup)
        acqPop.popup_frame.grid(row=0, column=0, sticky=(NSEW))

        #Creating content to put into popup frame
        acqPop.content = popup_entries(acqPop.popup_frame, acqPop)
        acqPop.content.grid(row=0, column=0, sticky=(NSEW))
        
    #Catching close buttons/destroying window procedures
        #Dismiss function for destroying window when done

    def dismiss(acqPop, verbose=False):
        acqPop.toplevel_acquire_popup.grab_release() #Ensures input can be anywhere now
        acqPop.toplevel_acquire_popup.destroy()