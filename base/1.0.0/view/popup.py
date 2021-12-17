from tkinter import *
import tkinter as tk
from tkinter import ttk
from view.notebooks.acquire_bar_frame.popup_entries import popup_entries

##TODO goal of this class is to create a generic popup that can be used for any purpose

#Class that handles the dialog box that has all the user entry stuff when you press the Acquisition button
class PopUp():

    def __init__(self, root, name, size, *args, **kwargs):
        #This starts the popup window config, and makes sure that any child widgets can be resized with the window
        self.popup = tk.Toplevel()
        self.popup.title(name)
        self.popup.geometry(size) #300x200 pixels, first +320 means 320 pixels from left edge, +180 means 180 pixels from top edge
        self.popup.columnconfigure(0, weight=1)
        self.popup.rowconfigure(0, weight=1)
        self.popup.resizable(FALSE, FALSE) #Makes it so user cannot resize
        self.popup.attributes("-topmost", 1) #Makes it be on top of mainapp when called
        
        self.popup.protocol("WM_DELETE_WINDOW", self.dismiss) #Intercepting close button
        self.popup.transient(root) #Prevents clicking outside of window
        self.popup.wait_visibility() # Can't grab until window appears, so we wait
        self.popup.grab_set()   #Ensures any input goes to this window

        #Putting popup frame into toplevel window
        self.popup_frame = ttk.Frame(self.popup)
        self.popup_frame.grid(row=0, column=0, sticky=(NSEW))

        #Creating content to put into popup frame
        self.content = popup_entries(self.popup_frame, self)
        self.content.grid(row=0, column=0, sticky=(NSEW))
        
    #Catching close buttons/destroying window procedures
        #Dismiss function for destroying window when done

    def dismiss(self, verbose=False):
        self.popup.grab_release() #Ensures input can be anywhere now
        self.popup.destroy()