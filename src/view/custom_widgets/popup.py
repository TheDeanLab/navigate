from tkinter import *
import tkinter as tk
from tkinter import ttk


## goal of this class is to create a generic popup that can be used for any purpose

#Class that handles the dialog box that has all the user entry stuff when you press the Acquisition button
class PopUp():

    def __init__(self, root, name, size, *args, **kwargs):
        '''
        #### Creates the popup window based on the root window being passed, title that you want the window to have and the size of the window.
        Some important things to consider:

        - Root has to be the main application window to work

        - Name has to be a string

        - Size also has to be a string in the format '600x400+320+180'

        - 600x400 represents the pixel size
        
        - +320 means 320 pixels from left edge, +180 means 180 pixels from top edge.

        - If a '-' is used insetead of '+' it will be from the opposite edge.

        - The parent frame for any widgets you add to the popup will be retrieved with the get_frame() function
        '''
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

        # The two below functions are examples of what we can use during testing
        self.popup.wait_visibility() # Can't grab until window appears, so we wait
        self.popup.grab_set()   #Ensures any input goes to this window

        #Putting popup frame into toplevel window
        self.content_frame = ttk.Frame(self.popup)
        self.content_frame.grid(row=0, column=0, sticky=(NSEW))

        # #Creating content to put into popup frame
        # self.content = popup_widgets(self.popup_frame, self)
        # self.content.grid(row=0, column=0, sticky=(NSEW))
        
    #Catching close buttons/destroying window procedures
        #Dismiss function for destroying window when done

    def dismiss(self, verbose=False):
        self.popup.grab_release() #Ensures input can be anywhere now
        self.popup.destroy()
    
    #Function so that popup entries can have a parent frame
    def get_frame(self):
        return self.content_frame