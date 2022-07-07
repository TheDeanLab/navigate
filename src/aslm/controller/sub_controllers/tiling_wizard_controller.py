"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

# Standard Library Imports
import logging

# Third Party Imports

# Local Imports
from aslm.controller.sub_controllers.gui_controller import GUI_Controller
from aslm.controller.aslm_controller_functions import combine_funcs

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Tiling_Wizard_Controller(GUI_Controller):
    """
    Controller for tiling wizard parameters.
    Gathers the FOV from the camera settings tab and will update when user changes this value.
    Set start/end position buttons will grab the stage values for the respective axis when pressed and display in popup
    Number of images we need to acquire with our desired percent overlap is calculated and then displayed in third column


    Parameters
    ----------
    view : object
        GUI element containing widgets and variables to control. Likely tk.Toplevel-derived. In this case tiling_wizard_popup.py
    parent_controller : channels_tab_controller
        The controller that creates the popup/this controller.
    verbose : bool, default False
        Display additional feedback in standard output.

    Returns
    -------
    None
    """

    def __init__(self,
                 view,
                 parent_controller,
                 verbose=False):
        super().__init__(view, parent_controller, verbose)

        # Getting widgets and buttons and vars of widgets
        self.widgets = self.view.get_widgets()
        self.buttons = self.view.get_buttons()
        self.variables = self.view.get_variables()

        # Init FOV from Camera Settings
        main_view = self.parent_controller.parent_controller.view # channels_tab_controller -> aslm_controller -> view
        self.cam_settings_widgets = main_view.settings.camera_settings_tab.camera_roi.get_widgets()
        self.fov = {'x': 0, 'y': 0}
        self.update_fov()

        # Trace cam_settings FOV to catch user changes
        self.cam_settings_widgets['FOV_X'].get_variable().trace_add('write', self.update_fov)
        self.cam_settings_widgets['FOV_Y'].get_variable().trace_add('write', self.update_fov)


        # Reference to access axis values in stage control tab
        self.stage_position_vars = main_view.stage_control.stage_control_tab.position_frame.get_variables()

        

        
        for axis in ['x', 'y', 'z']:

            # Start/End buttons
            self.buttons[axis + '_start'].configure(command=self.position_handler(axis, 'start'))
            self.buttons[axis + '_end'].configure(command=self.position_handler(axis, 'end'))

            # Init pos spinboxes to zero
            self.variables[axis + '_start'].set(0.0)
            self.variables[axis + '_end'].set(0.0)
            self.variables[axis + '_dist'].set(0.0)


        # Calculating distance
        self.variables['x_start'].trace_add('write', lambda *args: self.calculate_distance('x'))
        self.variables['x_end'].trace_add('write', lambda *args: self.calculate_distance('x'))
        self.variables['y_start'].trace_add('write', lambda *args: self.calculate_distance('y'))
        self.variables['y_end'].trace_add('write', lambda *args: self.calculate_distance('y'))
        self.variables['z_start'].trace_add('write', lambda *args: self.calculate_distance('z'))
        self.variables['z_end'].trace_add('write', lambda *args: self.calculate_distance('z'))


        # Setting/Tracing Percent Overlay
        self.percent_overlay = 0
        self.variables['percent_overlay'].trace_add('write', self.update_overlay)


        # Properly Closing Popup with parent controller
        self.view.popup.protocol("WM_DELETE_WINDOW", combine_funcs(self.view.popup.dismiss, lambda: delattr(self.parent_controller, 'tiling_wizard_controller')))

    
    def calculate_distance(self, axis):
        '''
        This function will calculate the distance for a given axis of the stage when the start or end position is changed via the Set buttons
        
        Parameters
        ----------
        self : object
            Tiling Wizard Controller instance
        axis : char
            x, y, z axis of stage to calculate

        Returns
        -------
        None

        '''

        start = float(self.variables[axis + '_start'].get())
        end = float(self.variables[axis + '_end'].get())
        dist = abs(end - start)
        self.variables[axis + '_dist'].set(dist)



        
   
    
    
    def update_overlay(self):
        '''
        Updates percent overlay when a user changes the widget in the popup. This value is used for backend calculations.

        Parameters
        ----------
        self : object
            Tiling Wizard Controller instance

        Returns
        -------
        None
        '''
        
        self.percent_overlay = self.variables['percent_overlay'].get()

    
    def position_handler(self, axis, start_end):
        '''
        When the Set [axis] Start/End button is pressed then the stage position is polled from the stage controller

        Parameters
        ----------
        self : object
            Tiling Wizard Controller instance
        axis : char
            x, y, z axis that corresponds to stage axis
        start_end : str
            start or end will signify which spinbox gets updated upon button press

        Returns
        -------
        handler : func
            Function for setting positional spinbox based on parameters passed in

        '''
        def handler():
            pos = self.stage_position_vars[axis].get()
            self.widgets[axis + '_' + start_end].widget.set(pos)
        return handler


    def update_fov(self):
        '''
        Grabs the updated FOV if changed by user
        '''
        x = self.cam_settings_widgets['FOV_X'].get()
        y = self.cam_settings_widgets['FOV_Y'].get()
        self.fov['x'] = x
        self.fov['y'] = y


    
    def showup(self):
        """
        # this function will let the popup window show in front
        """
        self.view.popup.deiconify()
        self.view.popup.attributes("-topmost", 1)