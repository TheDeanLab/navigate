#Think of tkinter as HTML, ttk as CSS, and Python as javascript
'''
A main window is created and passed to the mainapp class. This class will init as a frame then config the main window. It then 
creates a menubar using the menubar class. Adds the options for each file menu. It then sets up the frames, then grids the frames.
Finally it uses the notebook classes to put them into the respective frames on the grid. Each of the notebook classes includes tab 
classes and inits those etc. The second parameter in each classes __init__ function is the parent. I used the name of the parent
so that it would be easier to keep track of inheritances. Once you have the parent name you can look to the parents class in the 
class definition. For example for class Main_App(ttk.Frame) the parent to Main_App is a frame and its name is mainwin. I also used
the name of the class instead of self to make things easier to read. So for Main_App self is now mainapp.
'''

import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.constants import NSEW
from .settings_notebook_1 import settings_notebook as notebook_1
from .camera_waveform_notebook_2 import camera_waveform_notebook as notebook_2
from .stagecontrol_maxintensity_notebook_3 import stagecontrol_maxintensity_notebook as notebook_3


#Creates the frame that will hold the GUI content, its parent is the main window or root Tk object
class Main_App(ttk.Frame):
        #Takes a Tk object should be something like root = Tk() then root_window(root)
        def __init__(mainapp, mainwin, *args, **kwargs):
                #Inits this class as a frame subclass with the root/mainwin as its parent
                ttk.Frame.__init__(mainapp, mainwin, *args, **kwargs)
                #This starts the main window config, and makes sure that any child widgets can be resized with the window
                mainapp.mainwin = mainwin
                mainapp.mainwin.title("Super Ultimate Multiscale Microscope of the FUTURE!")
                mainapp.mainwin.minsize(1400,700)
                mainapp.mainwin.columnconfigure(0,weight=1)
                mainapp.mainwin.rowconfigure(0,weight=1)

                #Creating and linking menu to main window/app
                mainapp.menubar = menubar(mainwin)

                #File Menu
                mainapp.menu_file = Menu(mainapp.menubar)
                mainapp.menubar.add_cascade(menu=mainapp.menu_file, label='File')
                mainapp.menu_file.add_command(label='New')
                mainapp.menu_file.add_command(label='Open...')
                mainapp.menu_file.add_command(label='Close') #command=closeFile need this or some version to run action code

                #Edit Menu
                mainapp.menu_edit = Menu(mainapp.menubar)
                mainapp.menubar.add_cascade(menu=mainapp.menu_edit, label='Edit')
                mainapp.menu_edit.add_command(label='Copy')
                mainapp.menu_edit.add_command(label='Paste')

                #Left Frame Notebook 1 setup
                mainapp.frame_left = ttk.Frame(mainapp)
                mainapp.left_frame_label = ttk.Label(mainapp.frame_left, text="Notebook #1")
                mainapp.left_frame_label.pack()

                #Top right Frame Notebook 2 setup
                mainapp.frame_top_right = ttk.Frame(mainapp)
                mainapp.top_right_frame_label = ttk.Label(mainapp.frame_top_right, text="Notebook #2")
                mainapp.top_right_frame_label.pack()

                #Bottom right Frame Notebook 3 setup
                mainapp.frame_bottom_right = ttk.Frame(mainapp)
                mainapp.bottom_right_frame_label = ttk.Label(mainapp.frame_bottom_right, text="Notebook #3")
                mainapp.bottom_right_frame_label.pack()

                '''
                Placing the notebooks using grid. While the grid is called on each frame it is actually calling 
                the main window since those are the parent to the frames. The labels have already been packed into each respective
                frame so can be ignored in the grid setup. This layout uses a 2x2 grid to start. 

                        1   2
                        3   4 

                The above is the grid "spots" the left frame will take spots 1 & 3 while top right takes
                spot 2 and bottom right frame takes spot 4.
                '''

                #Gridding out foundational frames
                mainapp.grid(column=0, row=0, sticky=(NSEW)) #Sticky tells which walls of gridded cell the widget should stick to, in this case its sticking to the main window on all sides
                mainapp.frame_left.grid(row=0, column=0, rowspan=2, sticky=(NSEW))
                mainapp.frame_top_right.grid(row=0, column=1, sticky=(NSEW))
                mainapp.frame_bottom_right.grid(row=1, column=1, sticky=(NSEW))

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



#Menubar class
class menubar(Menu):
        def __init__(self, window, *args, **kwargs):
                #Init Menu with parent
                Menu.__init__(self, window, *args, **kwargs)
                #Creates operating system attribute
                self.opsystem = window.tk.call('tk', 'windowingsystem')
                #Prevents menu from tearing off bar
                window.option_add('*tearOff', False)
                #Linking menu to option of parent to this menu class
                window['menu'] = self


if __name__ == '__main__':
        root = tk.Tk()
        Main_App(root)
        root.mainloop()