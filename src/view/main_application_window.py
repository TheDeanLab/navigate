#Think of tkinter as HTML, ttk as CSS, and Python as javascript
'''
A main window is created and passed to the mainapp class. This class will init as a frame then config the main window. It then 
creates a menubar using the menubar class. Adds the options for each file menu. It then sets up the frames, then grids the frames.
Finally it uses the notebook classes to put them into the respective frames on the grid. Each of the notebook classes includes tab 
classes and inits those etc. The second parameter in each classes __init__ function is the parent. I used the name of the parent
so that it would be easier to keep track of inheritances. Once you have the parent name you can look to the parents class in the 
class definition. For example for class Main_App(ttk.Frame) the parent to Main_App is a frame and its name is root. I also used
the name of the class instead of self to make things easier to read. So for Main_App self is now mainapp.
'''
# Import Standard Libraries
import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.constants import NSEW

# Import Notebooks
from .main_window_content.settings_notebook import settings_notebook as notebook_1
from .main_window_content.camera_notebook import camera_waveform_notebook as notebook_2
from .main_window_content.stagecontrol_notebook import stagecontrol_maxintensity_notebook as notebook_3
from .main_window_content.acquire_bar_frame.acquire_bar import AcquireBar
from .main_window_content.menus import menubar

#Creates the frame that will hold the GUI content, its parent is the main window or root Tk object
class Main_App(ttk.Frame):
        #Takes a Tk object should be something like root = Tk() then root_window(root)

        def __init__(mainapp, root, *args, **kwargs):
                #Inits this class as a frame subclass with the root as its parent
                ttk.Frame.__init__(mainapp, root, *args, **kwargs)

                #This starts the main window config, and makes sure that any child widgets can be resized with the window
                mainapp.root = root
                mainapp.root.title("Multiscale Axially Swept Light-Sheet Microscope")
                program_directory = sys.path[0] #refers to script directory ie gets all the way down to view
                mainapp.root.iconphoto(True, PhotoImage(file=os.path.join(program_directory, "view", "icon", "mic.png")))
                mainapp.root.minsize(1400, 700)
                mainapp.root.columnconfigure(0,weight=1)
                mainapp.root.rowconfigure(0,weight=1)

                #Creating and linking menu to main window/app
                mainapp.menubar = menubar(root)

                #Top Frame Acquire Bar
                mainapp.top_frame = ttk.Frame(mainapp)
                #mainapp.top_frame_label = ttk.Label(mainapp.top_frame, text="Acquire Bar")
                #mainapp.top_frame_label.grid(row=0,column=0)

                #Left Frame Notebook 1 setup
                mainapp.frame_left = ttk.Frame(mainapp)
                #mainapp.left_frame_label = ttk.Label(mainapp.frame_left, text="Notebook #1")
                #mainapp.left_frame_label.grid(row=0,column=0)

                #Top right Frame Notebook 2 setup
                mainapp.frame_top_right = ttk.Frame(mainapp)
                #mainapp.top_right_frame_label = ttk.Label(mainapp.frame_top_right, text="Notebook #2")
                #mainapp.top_right_frame_label.grid(row=0,column=0)

                #Bottom right Frame Notebook 3 setup
                mainapp.frame_bottom_right = ttk.Frame(mainapp)
                #mainapp.bottom_right_frame_label = ttk.Label(mainapp.frame_bottom_right, text="Notebook #3")
                #mainapp.bottom_right_frame_label.grid(row=0,column=0)

                '''
                Placing the notebooks using grid. While the grid is called on each frame it is actually calling 
                the main window since those are the parent to the frames. The labels have already been packed into each respective
                frame so can be ignored in the grid setup. This layout uses a 2x2 grid to start. 

                        1   2
                        3   4
                        5   6 

                The above is the grid "spots" the left frame will take spots 3 & 5 while top right takes
                spot 4 and bottom right frame takes spot 6. Top frame will be spots 1 & 2
                '''

                #Gridding out foundational frames
                mainapp.grid(column=0, row=0, sticky=(NSEW)) #Sticky tells which walls of gridded cell the widget should stick to, in this case its sticking to the main window on all sides
                mainapp.top_frame.grid(row=0, column=0, columnspan=2, sticky=(NSEW))
                mainapp.frame_left.grid(row=1, column=0, rowspan=2, sticky=(NSEW))
                mainapp.frame_top_right.grid(row=1, column=1, sticky=(NSEW))
                mainapp.frame_bottom_right.grid(row=2, column=1, sticky=(NSEW))

                #This dictates how to weight each piece of the grid, so that when the window is resized the notebooks get the proper screen space. 
                # mainapp or mainapp is the frame holding all the other frames that hold the notebooks to help modularize the code
                mainapp.columnconfigure(0, weight=1) #can add an arg called min or max size to give starting point for each frame
                mainapp.columnconfigure(1, weight=1) #weights are relative to each other so if there is a 3 and 1 the 3 weight will give that col/row 3 pixels for every one the others get
                mainapp.rowconfigure(0, weight=1)
                mainapp.rowconfigure(1,weight=1)

                #Putting Notebooks into frames, tabs are held within the class of each notebook
                mainapp.notebook_1 = notebook_1(mainapp.frame_left)
                mainapp.notebook_2 = notebook_2(mainapp.frame_top_right)
                mainapp.notebook_3 = notebook_3(mainapp.frame_bottom_right)
                mainapp.acqbar = AcquireBar(mainapp.top_frame, mainapp.root)



if __name__ == '__main__':
        root = tk.Tk()
        Main_App(root)
        root.mainloop()