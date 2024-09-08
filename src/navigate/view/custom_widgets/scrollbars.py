# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below)
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
import tkinter.ttk as ttk
import platform

# Third Party Imports

# Local Imports


class ScrolledFrame(ttk.Frame):
    """A scrollable frame implemented in tkinter."""

    def __init__(self, parent, *args, **kw):
        """Initialize the ScrolledFrame.

        Parameters
        ----------
        root : Tk top-level widget
            Tkinter GUI instance to which this ScrolledFrame belongs.
        *args
            Additional arguments to pass to the ttk.Frame constructor.
        **kw
            Additional keyword arguments to pass to the ttk.Frame constructor.
        """
        ttk.Frame.__init__(self, parent, *args, **kw)

        # Create a canvas object and a vertical scrollbar for scrolling it.
        vscrollbar = ttk.Scrollbar(self, orient=tk.constants.VERTICAL)
        vscrollbar.pack(
            fill=tk.constants.Y, side=tk.constants.RIGHT, expand=tk.constants.FALSE
        )
        hscrollbar = ttk.Scrollbar(self, orient=tk.constants.HORIZONTAL)
        hscrollbar.pack(
            fill=tk.constants.X, side=tk.constants.BOTTOM, expand=tk.constants.FALSE
        )
        #: tk.Canvas: The canvas object for the ScrolledFrame.
        self.canvas = tk.Canvas(
            self,
            bd=0,
            highlightthickness=0,
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set,
            scrollregion=(0, 0, 100, 100),
        )
        self.canvas.pack(
            side=tk.constants.LEFT, fill=tk.constants.BOTH, expand=tk.constants.TRUE
        )
        vscrollbar.config(command=self.canvas.yview)
        hscrollbar.config(command=self.canvas.xview)

        # Reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # Create a frame inside the canvas which will be scrolled with it.
        #: ttk.Frame: The interior frame of the ScrolledFrame.
        self.interior = interior = ttk.Frame(self.canvas)
        _ = self.canvas.create_window(0, 0, window=interior, anchor=tk.constants.NW)

        # Track changes to the canvas and frame width and sync them,
        # also updating the scrollbar.
        def _configure_interior(event):
            """Configure the interior frame based on size changes.

            Updates the scrollbars to match the size of the inner frame, and updates
            the canvas width to fit the inner frame.

            Parameters
            ----------
            event : Tkinter Event
                The event triggering the configuration.
            """
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != self.canvas.winfo_width():
                self.canvas.config(width=interior.winfo_reqwidth())
            if interior.winfo_reqheight() != self.canvas.winfo_reqheight():
                self.canvas.config(height=interior.winfo_reqheight())

        interior.bind("<Configure>", _configure_interior)

    def mouse_wheel(self, event):
        """Handle the mouse wheel event for scrolling.

        Parameters
        ----------
        event : Tkinter Event
            The mouse wheel event.
        """
        delta = 120 if platform.system() != "Darwin" else 1
        shift = -1 * int(event.delta / delta)
        # TODO: event.state may only work on Mac (Darwin). Investigate for Windows.
        if event.state == 0:
            self.canvas.yview_scroll(shift, "units")
        elif event.state == 1:
            self.canvas.xview_scroll(shift, "units")
