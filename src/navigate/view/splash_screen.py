# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
import tkinter as tk

# Third Party Imports

# Local Imports


class SplashScreen(tk.Toplevel):
    """Display Splash Screen

    Briefly shows a splash screen upon loading the software.
    Centered depending upon the host computer being used.
    """

    def __init__(self, root: tk.Tk, image_path, *args, **kargs):
        """Initialize the SplashScreen.

        Parameters
        ----------
        root : tk.Tk
            Tkinter GUI instance to which this SplashScreen belongs.
        image_path : str
            Path to the image to display on the splash screen.
        *args
            Additional arguments to pass to the tk.Toplevel constructor.
        **kargs
            Additional keyword arguments to pass to the tk.Toplevel constructor.
        """

        tk.Toplevel.__init__(self, root)
        # without navigation panel
        self.overrideredirect(True)

        try:
            img = tk.PhotoImage(file=image_path)
            w, h = img.width(), img.height()  # width, height of the image
            loading_label = tk.Label(self, image=img)
        except tk.TclError:
            w, h = 300, 100
            loading_label = tk.Label(self, text="Loading Navigate Software ...")
        loading_label.pack()

        # get screen width and height
        ws = root.winfo_screenwidth()  # width of the screen
        hs = root.winfo_screenheight()  # height of the screen

        # calculate x and y coordinates for the Tk root window
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)

        # draw the window in the center of the window
        self.geometry("%dx%d+%d+%d" % (w, h, x, y))
        self.resizable(0, 0)
        self.update()
