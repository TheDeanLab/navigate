#__all__ = ['start_camera', 'start_stages', 'start_zoom_servo',
           #'start_filter_wheel', 'start_lasers', 'start_model']

# Standard library imports
import sys
from datetime import datetime
import os

# Third party imports
import numpy as np

# Local application imports
from model.aslm_model import Model
from view.notebooks.acquire_bar_frame.acquire_popup import Acquire_PopUp as acquire_popup

def start_model(configuration_path, verbose):
    """
    Initializes the Model.
    """
    global model
    model = Model(configuration_path, verbose)
    return model


def start_camera(self, camera_id, verbose):
    """
    Initializes the camera.
    """
    # Hamamatsu Camera
    if self.model.CameraParameters['type'] == 'HamamatsuOrca':
        from controller.devices.camera.Hamamatsu.HamamatsuCamera import Camera as CameraModel
        cam = CameraModel(camera_id, verbose)
        cam.initialize_camera()
        cam.set_exposure(model.CameraParameters['camera_exposure_time'])
        if verbose:
            print("Initialized ", model.CameraParameters['type'])

    # Synthetic Camera
    elif self.model.CameraParameters['type'] == 'SyntheticCamera':
        from controller.devices.camera.SyntheticCamera import Camera as CameraModel
        cam = CameraModel(0, verbose)
        cam.initialize_camera()
        cam.set_exposure(model.CameraParameters['camera_exposure_time'])
        if verbose:
            print("Initialized ", model.CameraParameters['type'])

    # Failed to Initialize
    else:
        print("Camera Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    return cam

def start_stages(self, verbose):
    """
    Initializes the Stage.
    """
    # Physik Instrumente Stage
    if self.model.StageParameters['stage_type'] == 'PI':
        from controller.devices.stages.PI.PIStage import Stage as StageModel
        stage = StageModel(self, verbose)
        if verbose:
            print("Initialized ", model.StageParameters['stage_type'])
        stage.report_position()

    # Synthetic Stage
    elif self.model.StageParameters['stage_type'] == 'SyntheticStage':
        from controller.devices.stages.SyntheticStage import Stage as StageModel
        stage = StageModel(self, verbose)
        if verbose:
            print("Initialized ", model.StageParameters['stage_type'])

    # Failed to Initialize
    else:
        print("Stage Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    return stage

def start_zoom_servo(self, verbose):
    """
    Initializes the Zoom Servo Motor
    """

    # Dynamixel Servo
    if self.model.ZoomParameters['zoom_type'] == 'Dynamixel':
        from controller.devices.zoom.Dynamixel.DynamixelZoom import Zoom as ZoomModel
        zoom = ZoomModel(self.model, verbose)
        if verbose:
            print("Initialized ", self.model.ZoomParameters['zoom_type'])
        print("Zoom Position", zoom.read_position())

    # Synthetic Servo
    elif self.model.ZoomParameters['zoom_type'] == 'SyntheticZoom':
        from controller.devices.zoom.SyntheticZoom import Zoom as ZoomModel
        zoom = ZoomModel(self.model, verbose)
        if verbose:
            print("Initialized ", self.model.ZoomParameters['zoom_type'])
        print("Zoom Position", zoom.read_position())
    else:
        print("Zoom Type in Configuration.yml Not Recognized - Initialization Failed")
        sys.exit()
    return zoom

def start_filter_wheel(model, verbose):
    pass

def start_lasers(model, verbose):
    pass

def launch_popup_window(self, root, verbose=False):
    """
    The popup window should only be launched if the microscope is set to save the data,
    with the exception of the continuous acquisition mode.
    """
    # Is the save data checkbox checked?
    save_data = self.view.notebook_1.channels_tab.stack_timepoint_frame.save_data.get()
    if save_data:

        # Are we in the continuous acquisition mode?
        if self.model.MicroscopeState['image_mode'] != 'continuous':

            # Launch the popup window
            popup_window = acquire_popup(root, verbose)

            # Configure the button callbacks on the popup window
            popup_window.content.cancel_btn.config(command=lambda: popup_window.dismiss(verbose))
            popup_window.content.done_btn.config(command=lambda: self.launch_acquisition(popup_window, verbose))

            # Populate the base path
            popup_window.content.root_entry_string.set(self.model.Saving['root_directory'])

            # Populate the user name
            if self.model.Saving['user'] is not None:
                popup_window.content.user_string.set(self.model.Saving['user'])

            # Populate the Tissue Type
            if self.model.Saving['tissue'] is not None:
                popup_window.content.tissue_string.set(self.model.Saving['tissue'])

            # Populate the Cell Type
            if self.model.Saving['celltype'] is not None:
                popup_window.content.celltype_string.set(self.model.Saving['celltype'])

            # Populate the Label Type
            if self.model.Saving['label'] is not None:
                popup_window.content.label_string.set(self.model.Saving['label'])

def populate_lasers(self, verbose=False):
    # Populate the laser list
    number_of_lasers = np.int(self.model.DAQParameters['number_of_lasers'])
    laser_list = []
    for i in range(number_of_lasers):
        laser_wavelength = self.model.DAQParameters['laser_'+str(i)+'_wavelength']
        laser_list.append(laser_wavelength)
    if verbose:
        print('Laser list: ', laser_list)
    return laser_list

def update_time_points(self, verbose=False):
    print("Updating time points")
    number_of_timepoints = self.view.notebook_1.channels_tab.stack_timepoint_frame.exp_time_spinval.get()
    self.model.MicroscopeState['timepoints'] = number_of_timepoints
    if verbose:
        print("Number of Timepoints:", session.MicroscopeState['timepoints'])

def update_z_steps(self, verbose=False):
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

    if verbose:
        print("Number of Z-Steps:", self.model.MicroscopeState['number_z_steps'])

def update_cycling_settings(self, verbose=False):
    '''
    Updates the cycling settings in the model and the GUI.
    '''
    # Update model
    self.model.MicroscopeState['stack_cycling_mode'] = self.view.notebook_1.channels_tab.stack_cycling_frame.cycling_options.get()
    if verbose:
        print("Cycling Mode:", self.model.MicroscopeState['stack_cycling_mode'])

def update_microscope_mode(self, verbose):
    microscope_state = self.view.acqbar.pull_down.get()
    if microscope_state == 'Continuous Scan':
        self.model.MicroscopeState['image_mode'] = 'continuous'
    elif microscope_state == 'Z-Stack':
        self.model.MicroscopeState['image_mode'] = 'z-stack'
    elif microscope_state == 'Single Acquisition':
        self.model.MicroscopeState['image_mode'] = 'single'
    elif microscope_state == 'Projection':
        self.model.MicroscopeState['image_mode'] = 'projection'
    if verbose:
        print("The Microscope State is now:", self.model.MicroscopeState['image_mode'])

def exit_program(self, verbose=False):
    if verbose:
        print("Exiting Program")
    sys.exit()

def create_save_path(self, popup_window, verbose=False):
    # Get the entries in the popup window.
    user_string = popup_window.content.user_string.get()
    tissue_string = popup_window.content.tissue_string.get()
    celltype_string = popup_window.content.celltype_string.get()
    label_string = popup_window.content.label_string.get()
    date_string = str(datetime.now().date())

    # Parse the entries in the popup window. Must be non-zero.
    if len(user_string) == 0:
        raise ValueError('Please provide a User Name')

    if len(tissue_string) == 0:
        raise ValueError('Please provide a Tissue Type')

    if len(celltype_string) == 0:
        raise ValueError('Please provide a Cell Type')

    if len(label_string) == 0:
        raise ValueError('Please provide a Label Type')

    # Make sure that there are no spaces in the variables
    user_string = user_string.replace(" ", "-")
    tissue_string = tissue_string.replace(" ", "-")
    celltype_string = celltype_string.replace(" ", "-")
    label_string = label_string.replace(" ", "-")

    # Create the save directory on disk.
    save_directory = os.path.join(self.model.Saving['root_directory'], user_string, tissue_string, celltype_string, label_string, date_string)
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Determine Number of Cells in Directory
    cell_index = 0
    cell_string = "Cell-" + str(cell_index).zfill(6)
    while os.path.exists(os.path.join(save_directory, cell_string)):
        cell_index += 1

    save_directory = os.path.join(self.model.Saving['root_directory'], user_string, tissue_string, celltype_string, label_string, date_string, cell_string)
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    if verbose:
        print("Data Will be Saved To:", save_directory)

    # Update the Model
    self.model.Saving = {
        'save_directory': save_directory,
        'user': user_string,
        'tissue': tissue_string,
        'celltype': celltype_string,
        'label': label_string,
        'date': date_string
    }

    return save_directory