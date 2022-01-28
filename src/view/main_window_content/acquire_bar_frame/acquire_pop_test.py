from tkinter import *
import tkinter as tk
from tkinter import ttk
from view.custom_widgets.popup import PopUp

class Acquire_PopUp():
     def __init__(self, root, *args, **kwargs):

         # Creating popup window with this name and size/placement
         self.popup = PopUp(root, "File Saving Dialog", '600x400+320+180')

         # Storing the content frame of the popup, this will be the parent of the widgets
         self.content_frame = self.popup.get_frame()

        #Widget Creation goes here