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
        """ Initialize the navigation style

        Note
        ----
        The style is based on the ttk style. More information found here:
        anzeljg.github.io/rin2/book2/2405/docs/tkinter/ttk-style-layer.html
        """
        s = ttk.Style()

        # Default font.
        s.configure('.', font=('Helvetica', 10))

        # Label frame labels.
        s.configure('TLabelframe.Label', font=('Helvetica', 16, 'bold'))

        # Tabs/Notebooks
        s.configure('TNotebook.Tab', font=('Helvetica', 12, 'bold'))

        # Labels
        s.configure(style='TLabel', font=('Helvetica', 12, 'bold', 'italic'))

        # Check buttons.
        s.configure('TCheckbutton', font=('Helvetica', 10))

        # Comboboxes.
        s.configure('TCombobox', font=('Helvetica', 10))


class SpinboxStyle:
    """ Style for spinbox in the navigation panel """
    def __init__(self):
        """ Initialize the spinbox style """
        self.font = tk.font.Font(family="Helvetica",
                                 size=10)