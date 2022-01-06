"""
This is the controller in an MVC-scheme for mediating the interaction between the View (GUI) and the model (./model/aslm_model.py).
Use: https://www.python-course.eu/tkinter_events_binds.php
"""

# Local Imports
from view.main_application_window import Main_App as view
from view.main_window_content.stage_control.stage_gui_controller import Stage_GUI_Controller
from controller.aslm_controller_functions import *
from model.aslm_model import Model

class ASLM_controller():
    def __init__(self, root, configuration_path, args):
        self.verbose = args.verbose

        # Initialize the Model
        global model
        self.model = Model(args, configuration_path)

        # Initialize the View
        self.view = view(root)

        #TODO: camera_view_tab, maximum intensity tab, waveform_tab
        # still need to be changed so that they are populated here.

        # Populate the View with the Model

        # Channels Tab, Channel Settings
        # Select only a single channel by default.
        self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[0].set(True)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[1].set(False)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[2].set(False)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[3].set(False)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.channel_variables[4].set(False)

        '''
        Loop to populate the channel settings******************************
        Code above and below that is commented out is no longer needed
        '''
        
        for x in range(5):
            self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[x]['values'] = populate_lasers(self, self.verbose)
            self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[x]['values'] = \
                list(self.model.session.FilterWheelParameters['available_filters'].keys())
            self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[x].set(self.model.session.StartupParameters['camera_exposure_time'])

        '''
        End of loop
        '''

        # Populate the lasers in the GUI
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[0]['values'] = populate_lasers(self, self.verbose)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[1]['values'] = populate_lasers(self)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[2]['values'] = populate_lasers(self)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[3]['values'] = populate_lasers(self)
        # self.view.notebook_1.channels_tab.channel_widgets_frame.laser_pulldowns[4]['values'] = populate_lasers(self)
        
            
        # Populate the filters in the GUI
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[0]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[1]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[2]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[3]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())
        # self.view.notebook_1.channels_tab.channel_widgets_frame.filterwheel_pulldowns[4]['values'] = \
        #     list(self.model.session.FilterWheelParameters['available_filters'].keys())

        # Populate the exposure times in the GUI
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[0].set(self.model.session.CameraParameters['camera_exposure_time'])
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[1].set(self.model.session.CameraParameters['camera_exposure_time'])
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[2].set(self.model.session.CameraParameters['camera_exposure_time'])
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[3].set(self.model.session.CameraParameters['camera_exposure_time'])
        # self.view.notebook_1.channels_tab.channel_widgets_frame.exptime_variables[4].set(self.model.session.CameraParameters['camera_exposure_time'])

        # Define all of the callbacks/events.
        # Acquire bar
        self.view.acqbar.acquire_btn.config(command=lambda: launch_popup_window(self, root, self.verbose))
        self.view.acqbar.exit_btn.config(command=lambda: exit_program(self.verbose))
        self.view.acqbar.pull_down.bind('<<ComboboxSelected>>', lambda *args: update_microscope_mode(self, self.verbose))

        # Channels Tab, Stack Acquisition Settings
        self.view.notebook_1.channels_tab.stack_acq_frame.start_pos_spinval.trace_add('write', lambda *args: update_z_steps(self, self.verbose))
        self.view.notebook_1.channels_tab.stack_acq_frame.step_size_spinval.trace_add('write', lambda *args: update_z_steps(self, self.verbose))
        self.view.notebook_1.channels_tab.stack_acq_frame.end_pos_spinval.trace_add('write', lambda *args: update_z_steps(self, self.verbose))

        # Channels Tab, Laser Cycling Settings
        self.view.notebook_1.channels_tab.stack_cycling_frame.cycling_options.trace_add('write', lambda *args: update_cycling_settings(self, self.verbose))

        # Channels Tab, Timepoint Settings
        self.view.notebook_1.channels_tab.stack_timepoint_frame.exp_time_spinval.trace_add('write', lambda *args: update_time_points(self, self.verbose))
        #TODO: Automatically calculate the stack acquisition time based on the number of timepoints, channels, and exposure time.

        # Channels Tab, Multi-position Acquisition Settings

        # Camera Tab, Camera Settings

        # Advanced Tab

        # Stage Controller
        self.stage_gui_controller = Stage_GUI_Controller(self.view.notebook_3.stage_control_tab, self)
        
        # Prepopulate the stage positions.
        stage_postion = self.model.session.StageParameters['position']
        self.stage_gui_controller.set_position({
            'x': stage_postion['x_pos'],
            'y': stage_postion['y_pos'],
            'z': stage_postion['z_pos'],
            'theta': stage_postion['theta_pos'],
            'f': stage_postion['f_pos']
        })

        # Prepopulate the stage step size.
        self.stage_gui_controller.set_step_size({
            'x': self.model.session.StageParameters['xy_step'],
            'z': self.model.session.StageParameters['z_step'],
            'theta': self.model.session.StageParameters['theta_step'],
            'f': self.model.session.StageParameters['f_step']
        })

        # Configure event control for the buttons
        self.view.menu_zoom.bind("<<MenuSelect>>", lambda *args: print("Zoom Selected", *args))


    def launch_acquisition(self, popup_window):
        # Need to create the save path, and update the model from the entries.
        save_directory = create_save_path(self, popup_window, self.verbose)

        #TODO: Acquire data according to the operating mode.

        # Close the window
        popup_window.dismiss(self.verbose)

    def execute(self, command, *args):
        '''
        This function listens to sub_gui_controllers
        '''
        print('command passed from child', command, args)
        if command == 'stage':
            # todo: call the model to move stage
            print('stage should move to', args[0], 'on', args[1])



if __name__ == '__main__':
    # Testing section.

    print("done")
