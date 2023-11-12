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
import logging

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)
"""
see:


"""


class Tooltip:
    """Create a tooltip for a given widget when the mouse hovers over it.

    http://stackoverflow.com/questions/3221956/
       what-is-the-simplest-way-to-make-tooltips-in-tkinter/36221216#36221216

    http://www.daniweb.com/programming/software-development/
           code/484591/a-tooltip-class-for-tkinter

    - Originally written by vegaseat on 2014.09.09.

    - Modified to include a delay time by Victor Zaccardo on 2016.03.25.

    - Modified
        - to correct extreme right and extreme bottom behavior,
        - to stay inside the screen whenever the tooltip might go out on
          the top but still the screen is higher than the tooltip,
        - to use the more flexible mouse positioning,
        - to add customizable background color, padding, waittime and
          wraplength on creation
      by Alberto Vassena on 2016.11.05.
    """

    def __init__(
        self,
        widget,
        *,
        bg="#FFFFEA",
        pad=(5, 3, 5, 3),
        text="widget info",
        waittime=400,
        wraplength=250
    ):
        """Initialize the ToolTip.

        Parameters
        ----------
        widget : tkinter widget
            The widget to which this tooltip is bound.
        bg : str, optional
            Background color for the tooltip. The default is "#FFFFEA".
        pad : tuple, optional
            Padding to be left around the text. The default is (5, 3, 5, 3).
        text : str, optional
            Text to be displayed in the tooltip. The default is "widget info".
        waittime : int, optional
            Delay in miliseconds before the tooltip shows up. The default is 400.
        wraplength : int, optional
            Wrap length for the tooltip text. The default is 250.
        """
        #: int: Delay in miliseconds before the tooltip shows up.
        self.waittime = waittime  # in miliseconds, originally 500
        #: int: Wrap length for the tooltip text.
        self.wraplength = wraplength  # in pixels, originally 180
        #: tk.Widget: The widget to which this tooltip is bound.
        self.widget = widget
        #: str: Text to be displayed in the tooltip.
        self.text = text
        # self.widget.bind("<Button-1>", self.onEnter)
        self.widget.bind("<Enter>", self.onEnter)
        self.widget.bind("<Leave>", self.onLeave)
        self.widget.bind("<ButtonPress>", self.onLeave)
        #: str: Background color for the tooltip.
        self.bg = bg
        #: tuple: Padding to be left around the text.
        self.pad = pad
        #: int: The id of the scheduled event.
        self.id = None
        #: tk.Toplevel: The tooltip toplevel.
        self.tw = None

    def onEnter(self, event=None):
        """Called when the mouse enters the widget.

        Parameters
        ----------
        event : tk.Event, optional
            The event that called this function. The default is None.
        """
        self.schedule()

    def onLeave(self, event=None):
        """Called when the mouse leaves the widget.

        Parameters
        ----------
        event : tk.Event, optional
            The event that called this function. The default is None.
        """
        self.unschedule()
        self.hide()

    def schedule(self):
        """Schedule the event."""
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        """Unschedule the event."""
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show(self):
        """Display the tooltip."""

        def tip_pos_calculator(widget, label, *, tip_delta=(10, 5), pad=(5, 3, 5, 3)):
            """Calculate the position of the tooltip on the screen.

            Parameters
            ----------
            widget : tk.Widget
                The widget to which this tooltip is bound.
            label : tk.Label
                The label containing the tooltip text.
            tip_delta : tuple, optional
                The offset of the tooltip from the mouse pointer.
                The default is (10, 5).
            pad : tuple, optional
                Padding to be left around the text. The default is (5, 3, 5, 3).

            Returns
            -------
            tuple
                The position of the tooltip on the screen.
            """

            w = widget

            s_width, s_height = w.winfo_screenwidth(), w.winfo_screenheight()

            width, height = (
                pad[0] + label.winfo_reqwidth() + pad[2],
                pad[1] + label.winfo_reqheight() + pad[3],
            )

            mouse_x, mouse_y = w.winfo_pointerxy()

            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height

            x_delta = x2 - s_width
            if x_delta < 0:
                x_delta = 0
            y_delta = y2 - s_height
            if y_delta < 0:
                y_delta = 0

            offscreen = (x_delta, y_delta) != (0, 0)

            if offscreen:

                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width

                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height

            offscreen_again = y1 < 0  # out on the top

            if offscreen_again:
                # No further checks will be done.

                # TIP:
                # A further mod might automagically augment the
                # wraplength when the tooltip is too high to be
                # kept inside the screen.
                y1 = 0

            return x1, y1

        bg = self.bg
        pad = self.pad
        widget = self.widget

        # creates a toplevel window
        self.tw = tk.Toplevel(widget)

        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)

        win = tk.Frame(self.tw, background=bg, borderwidth=0)
        label = tk.Label(
            win,
            text=self.text,
            justify=tk.LEFT,
            background=bg,
            relief=tk.SOLID,
            borderwidth=0,
            wraplength=self.wraplength,
        )

        label.grid(padx=(pad[0], pad[2]), pady=(pad[1], pad[3]), sticky=tk.NSEW)
        win.grid()

        x, y = tip_pos_calculator(widget, label)

        self.tw.wm_geometry("+%d+%d" % (x, y))

    def hide(self):
        """Hide the tooltip."""
        tw = self.tw
        if tw:
            tw.destroy()
        self.tw = None
