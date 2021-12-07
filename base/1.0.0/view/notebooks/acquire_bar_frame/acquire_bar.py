from tkinter import *
import tkinter as tk
from tkinter import ttk
from .acquire_popup import Acquire_PopUp
#from controller.acq_bar.acq_bar_controller import acqbar_controller


#Class for the acquisition bar found at the top of the main application window.
#Main function is to change acq setting and then call the acquisition top level window

class AcquireBar(ttk.Frame):

    def __init__(AcqBar, top_frame, root, session, verbose, *args, **kwargs):
        #Init bar with frame attr
        ttk.Frame.__init__(AcqBar, top_frame, *args, **kwargs)

        #Putting bar into frame
        AcqBar.grid(row=0, column=0)

        #Create command for popup to be called
        #TODO: Need an event tracker to update this. Should not pop up unless we are saving the data.
        # Should not pop up in the continuous mode.
        def detect_microscope_save_and_acquisition_state(session, verbose):
            if session.MicroscopeState['save_data'] == 0:
                def call_popup(session, verbose):
                    # Dummy function to not call the acquire_popup window.
                    pass
                if session.MicroscopeState['image_mode'] == 'continuous':
                    # Call function for continuous mode.
                    print("Continuous Mode")
                elif session.MicroscopeState['image_mode'] == 'z-stack':
                    # Call function for z-stack mode
                    print("Z-Stack Mode")
                elif session.MicroscopeState['image_mode'] == 'single':
                    # Call function for single acquisition mode
                    print("Single Mode")
                elif session.MicroscopeState['image_mode'] == 'projection':
                    # Call function for projection mode
                    print("Projection Mode")
            elif session.MicroscopeState['save_data'] == 1:
                if session.MicroscopeState['image_mode'] == 'continuous':
                    def call_popup(session, verbose):
                        # Dummy function to not call the acquire_popup window.
                        pass
                else:
                    def call_popup(session, verbose):
                        Acquire_PopUp(root, session)
            return call_popup

        call_popup = detect_microscope_save_and_acquisition_state(session, verbose)

        #Acquire Button
        AcqBar.acquire_btn = ttk.Button(AcqBar, text="Acquire", command=call_popup(session, verbose))

        #Read Only Pulldown menu: continuous, z-stack, single acquisition, projection.
        AcqBar.options = StringVar()
        AcqBar.pull_down = ttk.Combobox(AcqBar, textvariable=AcqBar.options)
        AcqBar.pull_down['values'] = ('Continuous Scan', 'Z-Stack', 'Single Acquisition', 'Projection')
        AcqBar.pull_down.current(0)
        AcqBar.pull_down.state(["readonly"])

        # Signal changes to the Acquisition Bar Pull Down Menu
        def signal_microscope_mode(AcqBar, session, verbose):
            microscope_state = AcqBar.pull_down.get()
            if microscope_state == 'Continuous Scan':
                session.MicroscopeState['image_mode'] = 'continuous'
            elif microscope_state == 'Z-Stack':
                session.MicroscopeState['image_mode'] = 'z-stack'
            elif microscope_state == 'Single Acquisition':
                session.MicroscopeState['image_mode'] = 'single'
            elif microscope_state == 'Projection':
                session.MicroscopeState['image_mode'] = 'projection'
            if verbose:
                print("The Microscope State is now:", session.MicroscopeState['image_mode'])

        #Update Session
        AcqBar.pull_down.bind('<<ComboboxSelected>>', lambda event: signal_microscope_mode(AcqBar, session, verbose))

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