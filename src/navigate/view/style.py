# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard library imports
import tkinter as tk
from tkinter import ttk

# Third-party imports

# Local application imports


class NavigateStyle:
    """ Style for check buttons in the navigation panel """
    def __init__(self):
        """ Initialize the check button style """

        # Default Style
        s = ttk.Style()
        s.configure('.', font=('Helvetica', 10))

        # Check Buttons
        self.style = ttk.Style()
        custom_font = tk.font.Font(size=3)
        self.style.configure(style="CustomCheckbutton.TCheckbutton",
                             font=custom_font)

        # Headers
        font = tk.font.Font(family="Helvetica",
                                 size=14,
                                 weight="bold")

        # Configure a custom style for the LabelFrame
        style = ttk.Style()
        style.configure("Custom.TLabelFrame.Label", font=font)
        style.configure("Custom.TLabelFrame", labelmargins=[20, 10, 10, 10])



    def get_style(self):
        """ Return the style """
        return self.style


class SpinboxStyle:
    """ Style for spinbox in the navigation panel """
    def __init__(self):
        """ Initialize the spinbox style """
        self.font = tk.font.Font(family="Helvetica",
                                 size=10)


class LabelStyle:
    """ Style for labels in the navigation panel """
    def __init__(self):
        """ Initialize the label style """
        self.font = tk.font.Font(family="Helvetica",
                                 size=12,
                                 weight="bold",
                                 slant="italic")


class HeaderStyle:
    """ Style for the header in the navigation panel """
    def __init__(self):
        """ Initialize the header style """
