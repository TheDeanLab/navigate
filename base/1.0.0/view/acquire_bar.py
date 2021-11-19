from tkinter import *
import tkinter as tk
from tkinter import ttk


#Class for the acquisition bar found at the top of the main application window. Main function is to change acq setting and then call the acquisition top level window

class AcquireBar(ttk.Frame):
    def __init__(AcqBar, top_frame, root, *args, **kwargs):
        #Init bar with frame attr
        ttk.Frame.__init__(AcqBar, top_frame, *args, **kwargs)
        #Putting bar into frame
        AcqBar.grid(row=0,column=0)

        #setting size etc
        

        #Creating each feature of bar

        #Create command for popup to be called
        def callPop():
            Acquire_PopUp(root)
            

        #Acquire Button
        AcqBar.acquire_btn = ttk.Button(
            AcqBar,
            text="Acquire",
            command=callPop
        )

        #Pulldown menu: continuous, z-stack, single acquisition, projection. Uses a combobox that restricts item choice
        AcqBar.options = StringVar()
        AcqBar.pull_down = ttk.Combobox(AcqBar, textvariable=AcqBar.options)
        AcqBar.pull_down['values'] = ('Continuous Scan', 'Z-Stack', 'Single Acquisition', 'Projection')
        AcqBar.pull_down.state(["readonly"]) #Makes it so the user cannot type a choice into combobox

        #Progess Bar: Current Acquitiions and Overall
        AcqBar.progBar_frame = ttk.Frame(AcqBar) #This is used to hold and grid the two progess bars.Now when this is loaded into Acbar the progress bars will follow
        AcqBar.CurAcq = ttk.Progressbar(AcqBar.progBar_frame, orient=HORIZONTAL, length=200, mode='indeterminate') #Change mode to determinate and set steps for more intuitive usage
        AcqBar.OvrAcq = ttk.Progressbar(AcqBar.progBar_frame, orient=HORIZONTAL, length=200, mode='indeterminate')
        AcqBar.CurAcq.grid(row=0,column=0)
        AcqBar.OvrAcq.grid(row=1,column=0)  

        #Exit Button
        AcqBar.exit_btn = ttk.Button(
            AcqBar,
            text="Exit"
            #command=
        )

        #Gridding out Bar
        '''
            0   1   2   3
        '''
        AcqBar.acquire_btn.grid(row=0, column=0, sticky=(NSEW))
        AcqBar.pull_down.grid(row=0, column=1, sticky=(NSEW))
        AcqBar.progBar_frame.grid(row=0, column=2, sticky=(NSEW))
        AcqBar.exit_btn.grid(row=0, column=3, sticky=(NSEW))


class Acquire_PopUp():
    def __init__(acqPop,root, *args, **kwargs):
        #This starts the popup window config, and makes sure that any child widgets can be resized with the window
        acqPop.toplevel_acquire_popup = tk.Toplevel()
        acqPop.toplevel_acquire_popup.title("Acquisition Dialog")
        acqPop.toplevel_acquire_popup.geometry('600x400+320+180') #300x200 pixels, first +320 means 320 pixels from left edge, +180 means 180 pixels from top edge
        acqPop.toplevel_acquire_popup.columnconfigure(0,weight=1)
        acqPop.toplevel_acquire_popup.rowconfigure(0,weight=1)
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
        acqPop.content.grid(row=0,column=0, sticky=(NSEW))
        
    #Catching close buttons/destroying window procedures
        #Dismiss function for destroying window when done
    def dismiss(acqPop):
        acqPop.toplevel_acquire_popup.grab_release() #Ensures input can be anywhere now
        acqPop.toplevel_acquire_popup.destroy()

class popup_entries(ttk.Frame):
    def __init__(content, popup, toplevel, *args, **kwargs):
        #Init content with frame attr
        ttk.Frame.__init__(content, popup, *args, **kwargs)

        #Setting up entries and Done/Cancel button

        #Label for entries
        content.entries_label = ttk.Label(content, text="Please fill out the fields below")

        #User Entry
        content.user_entry_frame = ttk.Frame(content)
        content.user_entry = ttk.Entry(content.user_entry_frame, width=15)
        content.user_entry_label = ttk.Label(content.user_entry_frame, text="User")
        content.user_entry_label.grid(row=0, column=0, sticky="e")
        content.user_entry.grid(row=0, column=1, sticky="w")

        #Tissue Entry
        content.tissue_entry_frame = ttk.Frame(content)
        content.tissue_entry = ttk.Entry(content.tissue_entry_frame, width=15)
        content.tissue_entry_label = ttk.Label(content.tissue_entry_frame, text="Tissue")
        content.tissue_entry_label.grid(row=0, column=0, sticky="e")
        content.tissue_entry.grid(row=0, column=1, sticky="w")

        #Cell Type Entry
        content.celltype_entry_frame = ttk.Frame(content)
        content.celltype_entry = ttk.Entry(content.celltype_entry_frame, width=15)
        content.celltype_entry_label = ttk.Label(content.celltype_entry_frame, text="Cell Type")
        content.celltype_entry_label.grid(row=0, column=0, sticky="e")
        content.celltype_entry.grid(row=0, column=1, sticky="w")

        #Label Entry
        content.label_entry_frame = ttk.Frame(content)
        content.label_entry = ttk.Entry(content.label_entry_frame, width=15)
        content.label_entry_label = ttk.Label(content.label_entry_frame, text="Label")
        content.label_entry_label.grid(row=0, column=0, sticky="e")
        content.label_entry.grid(row=0, column=1, sticky="w")

        #Cell Number Entry
        content.cellnum_entry_frame = ttk.Frame(content)
        content.cellnum_entry = ttk.Entry(content.cellnum_entry_frame, width=15)
        content.cellnum_entry_label = ttk.Label(content.cellnum_entry_frame, text="Cell Number")
        content.cellnum_entry_label.grid(row=0, column=0, sticky="e")
        content.cellnum_entry.grid(row=0, column=1, sticky="w")

        #Date Entry (will be prepopulated)
        content.date_entry_frame = ttk.Frame(content)
        content.date_entry = ttk.Entry(content.date_entry_frame, width=15)
        content.date_entry_label = ttk.Label(content.date_entry_frame, text="Date")
        content.date_entry_label.grid(row=0, column=0, sticky="e")
        content.date_entry.grid(row=0, column=1, sticky="w")

        #Done and Cancel Buttons
        content.done_btn = ttk.Button(
            content, 
            text="Done" 
            #command=toplevel.dismiss #Will call the Aquire_Popup class dismiss function toplevel is acqPop above
        ) #Will need more code to use inputs to generate path for directory
        content.cancel_btn = ttk.Button(
            content, 
            text="Cancel" 
            #command=toplevel.dismiss
        ) #Will need more code for not using input given
        #Assign a lambda to the button command, passing whatever you want into that function.
        #command=lambda: whatver(pass_your_data_from_entry)

        #Gridding out entries and buttons
        '''
        Grid for buttons

                00  01
                02  03
                04  05 
                06  07
                08  09
                10  11
                12  13

        Entries Label is 00,01
        User Entry is 02,03
        Tissue is 04,05
        Cell Type is 06,07
        Label is 08,09
        Cell Number is 10,11
        Cancel btn is 12
        Done btn is 13
        '''

        content.entries_label.grid(row=0, column=0, columnspan=2, sticky=(NSEW))
        content.user_entry_frame.grid(row=1, column=0, columnspan=2, sticky=(NSEW))
        content.tissue_entry_frame.grid(row=2, column=0, columnspan=2, sticky=(NSEW))
        content.celltype_entry_frame.grid(row=3, column=0, columnspan=2, sticky=(NSEW))
        content.label_entry_frame.grid(row=4, column=0, columnspan=2, sticky=(NSEW))
        content.cellnum_entry_frame.grid(row=5, column=0, columnspan=2, sticky=(NSEW))
        content.cancel_btn.grid(row=6, column=0, sticky=(NSEW))
        content.done_btn.grid(row=6, column=1, sticky=(NSEW))