"""
ASLM sub-controller ETL popup window.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

from aslm.controller.sub_controllers.gui_controller import GUI_Controller
from aslm.controller.aslm_controller_functions import combine_funcs


import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Tiling_Wizard_Controller(GUI_Controller):
    def __init__(self, view, parent_controller, verbose=False):
        """
        Controller for tiling wizard parameters.

        Parameters
        ----------
        view : object
            GUI element containing widgets and variables to control. Likely tk.Toplevel-derived.
        parent_controller : ASLM_controller
            The main controller.
        verbose : bool, default False
            Display additional feedback in standard output.

        Returns
        -------
        None
        """

        super().__init__(view, parent_controller, verbose)

        # Getting widgets and buttons and vars of widgets
        self.widgets = self.view.get_widgets()
        self.buttons = self.view.get_buttons()
        self.variables = self.view.get_variables()

        # Add controller code here


        # Properly Closing Popup with parent controller
        self.view.popup.protocol("WM_DELETE_WINDOW", combine_funcs(self.view.popup.dismiss, lambda: delattr(self.parent_controller, 'tiling_wizard_controller')))