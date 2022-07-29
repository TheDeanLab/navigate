
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.constants import *



# Based on
#   https://web.archive.org/web/20170514022131id_/http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame

class ScrolledFrame(ttk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame.
    * Construct and pack/place/grid normally.
    * This frame only allows vertical scrolling.
    """
    def __init__(self, parent, *args, **kw):
            ttk.Frame.__init__(self, parent, *args, **kw)

            # Create a canvas object and a vertical scrollbar for scrolling it.
            vscrollbar = ttk.Scrollbar(self, orient=VERTICAL)
            vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
            hscrollbar = ttk.Scrollbar(self, orient=HORIZONTAL)
            hscrollbar.pack(fill=X, side=BOTTOM, expand=FALSE)
            canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                            yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set, scrollregion=(0, 0, 100, 100))
            canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
            vscrollbar.config(command=canvas.yview)
            hscrollbar.config(command=canvas.xview)

            # Reset the view
            canvas.xview_moveto(0)
            canvas.yview_moveto(0)

            # Create a frame inside the canvas which will be scrolled with it.
            self.interior = interior = ttk.Frame(canvas)
            interior_id = canvas.create_window(0, 0, window=interior,
                                            anchor=NW)

            # Track changes to the canvas and frame width and sync them,
            # also updating the scrollbar.
            def _configure_interior(event):
                # Update the scrollbars to match the size of the inner frame.
                size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
                canvas.config(scrollregion="0 0 %s %s" % size)
                if interior.winfo_reqwidth() != canvas.winfo_width():
                    # Update the canvas's width to fit the inner frame.
                    canvas.config(width=interior.winfo_reqwidth())
                if interior.winfo_reqheight() != canvas.winfo_reqheight():
                    canvas.config(height=interior.winfo_reqheight())
            interior.bind('<Configure>', _configure_interior)

