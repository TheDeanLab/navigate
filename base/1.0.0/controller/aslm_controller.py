"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model (./model/aslm_model.py).
Use: https://www.python-course.eu/tkinter_events_binds.php
"""

# Import Standard Python Packages
import numpy as np

# Local Imports
from view.main_application_window import Main_App as ASLM_view
from controller.initialization_functions import *

class ASLM_controller():
    def __init__(self, root, configuration_path, verbose):
        if verbose:
            print("Starting ASLM_controller")

        # Initialize the Model
        self.configuration_path = configuration_path
        self.model = start_model(self.configuration_path, verbose)

        # Initialize Hardware Devices
        self.camera_id = 0
        self.cam = start_camera(self.model, self.camera_id, verbose)

        # Initialize the View
        self.view = ASLM_view(root, self.model, self.cam, verbose)

        # CALLBACKS

        # Channels Tab, Channel Settings

        # Channels Tab, Stack Acquisition Settings
        self.view.notebook_1.channels_tab.stack_acq_frame.start_pos_spinval.trace_add('write', lambda *args: self.update_z_steps())
        self.view.notebook_1.channels_tab.stack_acq_frame.step_size_spinval.trace_add('write', lambda *args: self.update_z_steps())
        self.view.notebook_1.channels_tab.stack_acq_frame.end_pos_spinval.trace_add('write', lambda *args: self.update_z_steps())

        # Channels Tab, Laser Cycling Settings

        # Channels Tab, Timepoint Settings

        # Channels Tab, Multi-position Acquisition Settings

        # Camera Tab, Camera Settings

        # Advanced Tab

    def update_z_steps(self):
        '''
        Recalculates the number of slices that will be acquired in a z-stack whenever the GUI
        has the start position, end position, or step size changed.
        Sets the number of slices in the model and the GUI.
        '''
        # Calculate the number of slices and set GUI
        start_position = np.float(self.view.notebook_1.channels_tab.stack_acq_frame.start_pos_spinval.get())
        end_position = np.float(self.view.notebook_1.channels_tab.stack_acq_frame.end_pos_spinval.get())
        step_size = np.float(self.view.notebook_1.channels_tab.stack_acq_frame.step_size_spinval.get())
        number_z_steps = np.floor((end_position - start_position)/step_size)
        self.view.notebook_1.channels_tab.stack_acq_frame.slice_spinbox.set(number_z_steps)

        # Update model
        self.model.MicroscopeState['step_size'] = step_size
        self.model.MicroscopeState['start_position'] = start_position
        self.model.MicroscopeState['end_position'] = end_position
        self.model.MicroscopeState['number_z_steps'] = number_z_steps





if __name__ == '__main__':
    # Testing section.

    print("done")





