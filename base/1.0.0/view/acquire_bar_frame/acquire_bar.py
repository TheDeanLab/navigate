from tkinter import *
import tkinter as tk
from tkinter import ttk
from .acquire_popup import Acquire_PopUp
#from controller.acq_bar.acq_bar_controller import acqbar_controller


#Class for the acquisition bar found at the top of the main application window.
#Main function is to change acq setting and then call the acquisition top level window

class AcquireBar(ttk.Frame):

    def __init__(AcqBar, top_frame, root, session, *args, **kwargs):
        #Init bar with frame attr
        ttk.Frame.__init__(AcqBar, top_frame, *args, **kwargs)
        #Putting bar into frame
        AcqBar.grid(row=0,column=0)

        #setting size etc
        

        #Creating each feature of bar

        #Create command for popup to be called
        def callPop():
            Acquire_PopUp(root, session)

        #Acquire Button
        AcqBar.acquire_btn = ttk.Button(AcqBar, text="Acquire", command=callPop)

        #Pulldown menu: continuous, z-stack, single acquisition, projection. Uses a combobox that restricts item choice
        AcqBar.options = StringVar()
        AcqBar.pull_down = ttk.Combobox(AcqBar, textvariable=AcqBar.options)
        AcqBar.pull_down['values'] = ('Continuous Scan', 'Z-Stack', 'Single Acquisition', 'Projection')
        AcqBar.pull_down.current(0)
        AcqBar.pull_down.state(["readonly"]) #Makes it so the user cannot type a choice into combobox
        

        #Progess Bar: Current Acquitiions and Overall
        AcqBar.progBar_frame = ttk.Frame(AcqBar)
        #This is used to hold and grid the two progess bars.Now when this is loaded into Acbar the progress bars will follow
        AcqBar.CurAcq = ttk.Progressbar(AcqBar.progBar_frame, orient=HORIZONTAL, length=200, mode='indeterminate')
        #Change mode to determinate and set steps for more intuitive usage
        AcqBar.OvrAcq = ttk.Progressbar(AcqBar.progBar_frame, orient=HORIZONTAL, length=200, mode='indeterminate')
        AcqBar.CurAcq.grid(row=0,column=0)
        AcqBar.OvrAcq.grid(row=1,column=0)

        def exit_program():
            print("Shutting Down Program")
            sys.exit()

        #Exit Button
        AcqBar.exit_btn = ttk.Button(AcqBar, text="Exit", command=exit_program)

        #Gridding out Bar
        '''
            0   1   2   3
        '''
        AcqBar.acquire_btn.grid(row=0, column=0, sticky=(NSEW))
        AcqBar.pull_down.grid(row=0, column=1, sticky=(NSEW))
        AcqBar.progBar_frame.grid(row=0, column=2, sticky=(NSEW))
        AcqBar.exit_btn.grid(row=0, column=3, sticky=(NSEW))

        #Passing controller the setup frame
        #acqbar_controller(AcqBar)