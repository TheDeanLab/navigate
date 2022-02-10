from tkinter import *
from tkinter import ttk



class AcquireBar(ttk.Frame):
    """
    #  Class for the acquisition bar found at the top of the main application window.
    #  Main function is to change acq setting and then call the acquisition top level window
    """
    def __init__(self, top_frame, root, *args, **kwargs):
        #  Init bar with frame attr
        ttk.Frame.__init__(self, top_frame, *args, **kwargs)

        #  Putting bar into frame
        self.grid(row=0, column=0)

        #  Acquire Button
        self.acquire_btn = ttk.Button(self, text="Acquire")

        #  Read Only Pull down menu: continuous, z-stack, single acquisition, projection.
        self.options = StringVar()
        self.pull_down = ttk.Combobox(self, textvariable=self.options)
        self.pull_down['values'] = ('Continuous Scan', 'Z-Stack', 'Single Acquisition', 'Alignment', 'Projection')
        self.pull_down.current(0)
        self.pull_down.state(["readonly"])

        #  Progress Bar: Current Acquisitions and Overall
        self.progBar_frame = ttk.Frame(self)

        #  This is used to hold and grid the two progress bars.Now when this is
        #  loaded into Acbar the progress bars will follow
        self.CurAcq = ttk.Progressbar(self.progBar_frame, orient=HORIZONTAL, length=200, mode='indeterminate')

        #  Change mode to determinate and set steps for more intuitive usage
        self.OvrAcq = ttk.Progressbar(self.progBar_frame, orient=HORIZONTAL, length=200, mode='indeterminate')
        self.CurAcq.grid(row=0, column=0)
        self.OvrAcq.grid(row=1, column=0)

        #  Exit Button
        self.exit_btn = ttk.Button(self, text="Exit")

        #  Gridding out Bar
        '''
            0   1   2   3
        '''
        self.acquire_btn.grid(row=0, column=0, sticky=NSEW)
        self.pull_down.grid(row=0, column=1, sticky=NSEW)
        self.progBar_frame.grid(row=0, column=2, sticky=NSEW)
        self.exit_btn.grid(row=0, column=3, sticky=NSEW)
