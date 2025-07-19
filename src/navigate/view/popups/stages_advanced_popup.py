# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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

# Local Imports
from navigate.view.custom_widgets.popup import PopUp


class StageLimitsPopup:
    """Class creates the popup to set stage limits."""

    def __init__(self, root, *args, **kwargs):
        """Initialize the CameraSettingPopup class.

        Parameters
        ----------
        root : tkinter.Tk
            Root window of the application.
        args : list
            List of arguments.
        kwargs : dict
            Dictionary of keyword arguments.
        """
        # Creating popup window with this name and size/placement, PopUp is a
        # Toplevel window
        #: PopUp: Popup window for the camera view.
        self.popup = PopUp(
            root,
            name="Stage Limits",
            size="+320+180",
            top=False,
            transient=False,
        )
        self.popup.resizable(tk.TRUE, tk.TRUE)

        # Creating the frame for the popup
        self.frame = self.popup.content_frame

        # Add tk labels to the frame
        # Column 1, stage identity. Column 2, minimum limit. Column 3, update button.
        # Column 4, maximum limit. Column 5, update button.

        # Create column headers
        tk.Label(self.frame, text="Stage", font=("Arial", 10, "bold")).grid(
            row=0, column=0, padx=5, pady=5, sticky="NSEW"
        )
        tk.Label(self.frame, text="Minimum Limit", font=("Arial", 10, "bold")).grid(
            row=0, column=1, columnspan=2, padx=5, pady=5, sticky="NSEW"
        )
        tk.Label(self.frame, text="Maximum Limit", font=("Arial", 10, "bold")).grid(
            row=0, column=3, columnspan=2, padx=5, pady=5, sticky="NSEW"
        )

        # Trace for when the popup is closed
        self.popup.protocol("WM_DELETE_WINDOW", self.close_popup)

    def populate_view(self, stages):
        """Populate the view with the stages.

        Add the widgets to the view for each stage in alphabetical order.
        Creates a row for each stage with: stage name, min limit spinbox,
        update min button, max limit spinbox, and update max button.

        Parameters
        ----------
        stages : list
            List of stage names as strings.
        """
        # Sort stages alphabetically
        sorted_stages = sorted(stages)

        # Create a row for each stage
        for i, stage_name in enumerate(sorted_stages, start=1):
            # Column 1: Stage name label
            tk.Label(self.frame, text=stage_name).grid(
                row=i, column=0, padx=5, pady=2, sticky="w"
            )

            # Column 2: Minimum limit spinbox
            min_spinbox = tk.Spinbox(
                self.frame,
                from_=-10000,
                to=10000,
                width=10,
                format="%.3f",
                increment=0.1,
            )
            min_spinbox.grid(row=i, column=1, padx=5, pady=2)

            # Column 3: Update minimum button
            update_min_btn = tk.Button(self.frame, text="Update", width=8)
            update_min_btn.grid(row=i, column=2, padx=5, pady=2)

            # Column 4: Maximum limit spinbox
            max_spinbox = tk.Spinbox(
                self.frame,
                from_=-10000,
                to=10000,
                width=10,
                format="%.3f",
                increment=0.1,
            )
            max_spinbox.grid(row=i, column=3, padx=5, pady=2)

            # Column 5: Update maximum button
            update_max_btn = tk.Button(self.frame, text="Update", width=8)
            update_max_btn.grid(row=i, column=4, padx=5, pady=2)

    def close_popup(self):
        """Close the popup window."""
        self.popup.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    popup = StageLimitsPopup(root)
    popup.populate_view(["Stage 1", "Stage 2", "Stage 3"])
    popup.popup.mainloop()
