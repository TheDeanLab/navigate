"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model (./model/aslm_model.py).
Use: https://www.python-course.eu/tkinter_events_binds.php
"""
import sys

# Import Standard Python Packages
import numpy as np

# Local Imports
from view.main_application_window import Main_App as view
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
        self.view = view(root)

        # CALLBACKS
        # ACQUIRE BAR
        self.view.acqbar.acquire_btn.config(command=lambda: self.call_popup(self))
        self.view.acqbar.exit_btn.config(command=lambda: self.exit_program())

        #AcqBar.pull_down.bind('<<ComboboxSelected>>', lambda event: signal_microscope_mode(AcqBar, session, verbose))
        #AcqBar.acquire_btn = ttk.Button(AcqBar, text="Acquire", command=call_popup)


        # Channels Tab, Channel Settings
        self.view.notebook_1.channels_tab.channel_1_frame.laser_pull_down['values'] = self.populate_lasers()
        self.view.notebook_1.channels_tab.channel_2_frame.laser_pull_down['values'] = self.populate_lasers()
        self.view.notebook_1.channels_tab.channel_3_frame.laser_pull_down['values'] = self.populate_lasers()
        self.view.notebook_1.channels_tab.channel_4_frame.laser_pull_down['values'] = self.populate_lasers()
        self.view.notebook_1.channels_tab.channel_5_frame.laser_pull_down['values'] = self.populate_lasers()

        self.view.notebook_1.channels_tab.channel_1_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())
        self.view.notebook_1.channels_tab.channel_2_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())
        self.view.notebook_1.channels_tab.channel_3_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())
        self.view.notebook_1.channels_tab.channel_4_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())
        self.view.notebook_1.channels_tab.channel_5_frame.filterwheel_pull_down['values'] = \
            list(self.model.FilterWheelParameters['available_filters'].keys())


        #  list(filter_dictionary.keys())



        # Channels Tab, Stack Acquisition Settings
        self.view.notebook_1.channels_tab.stack_acq_frame.start_pos_spinval.trace_add('write', lambda *args: self.update_z_steps())
        self.view.notebook_1.channels_tab.stack_acq_frame.step_size_spinval.trace_add('write', lambda *args: self.update_z_steps())
        self.view.notebook_1.channels_tab.stack_acq_frame.end_pos_spinval.trace_add('write', lambda *args: self.update_z_steps())

        # Channels Tab, Laser Cycling Settings

        # Channels Tab, Timepoint Settings
        self.view.notebook_1.channels_tab.stack_timepoint_frame.exp_time_spinval.trace_add('write', lambda *args: self.update_time_points())
        #TODO: Update the MicroscopeState['save_data'] variable when the user changes the save_data_checkbox
        #Not sure how to do this with checkboxes.
        #self.view.notebook_1.channels_tab.stack_timepoint_frame.save_check.variable.trace_add('write', lambda *args: self.update_save_data())


        # Channels Tab, Multi-position Acquisition Settings

        # Camera Tab, Camera Settings

        # Advanced Tab

    def populate_lasers(self):
        # Populate the laser list
        number_of_lasers = np.int(self.model.DAQParameters['number_of_lasers'])
        laser_list = []
        for i in range(number_of_lasers):
            laser_wavelength = self.model.DAQParameters['laser_'+str(i)+'_wavelength']
            laser_list.append(laser_wavelength)
        return laser_list

    def update_time_points(self, verbose=False):
        print("Updating time points")
        number_of_timepoints = self.view.notebook_1.channels_tab.stack_timepoint_frame.exp_time_spinval.get()
        self.model.MicroscopeState['timepoints'] = number_of_timepoints
        if verbose:
            print("Number of Timepoints:", session.MicroscopeState['timepoints'])

    def update_save_data(self, verbose=False):
        print("hellO?")
        if self.view.notebook_1.channels_tab.stack_timepoint_frame.save_data_checkbox.get() == False:
            self.model.MicroscopeState['save_data'] = 0
        else:
            self.model.MicroscopeState['save_data'] = 1
        if verbose:
            print("Save Data State:", session.MicroscopeState['save_data'])

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


    # ACQUISITION BAR FUNCTION
    # Signal changes to the Acquisition Bar Pull Down Menu
    def signal_microscope_mode(AcqBar, session, verbose):
        microscope_state = AcqBar.pull_down.get()
        if microscope_state == 'Continuous Scan':
            session.MicroscopeState['image_mode'] = 'continuous'
        elif microscope_state == 'Z-Stack':
            session.MicroscopeState['image_mode'] = 'z-stack'
        elif microscope_state == 'Single Acquisition':
            session.MicroscopeState['image_mode'] = 'single'
        elif microscope_state == 'Projection':
            session.MicroscopeState['image_mode'] = 'projection'
        if verbose:
            print("The Microscope State is now:", session.MicroscopeState['image_mode'])

    #Create command for popup to be called
    def call_popup(session):
        Acquire_PopUp(root, session)


    def exit_program(self):
        print("Shutting Down Program")
        sys.exit()

if __name__ == '__main__':
    # Testing section.

    print("done")
