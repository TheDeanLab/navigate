# Standard library imports
from datetime import datetime
import os

def create_save_path(saving_settings, verbose=False):
    """
    # haven't finished
    # This function retrieves the user inputs from the popup save window.
    # It then creates a new directory in the user specified path.
    """
    root_directory = saving_settings['root_directory']
    user_string = saving_settings['user']
    tissue_string = saving_settings['tissue']
    celltype_string = saving_settings['celltype']
    label_string = saving_settings['label']
    date_string = str(datetime.now().date())

    # Make sure that there are no spaces in the variables
    user_string = user_string.replace(" ", "-")
    tissue_string = tissue_string.replace(" ", "-")
    celltype_string = celltype_string.replace(" ", "-")
    label_string = label_string.replace(" ", "-")

    # Create the save directory on disk.
    save_directory = os.path.join(saving_settings['root_directory'],
                                  user_string,
                                  tissue_string,
                                  celltype_string,
                                  label_string,
                                  date_string)
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Determine Number of Cells in Directory
    cell_directories = list(filter(lambda v: v[:5] == 'Cell_', os.listdir(save_directory)))
    if len(cell_directories) != 0:
        cell_directories.sort()
        cell_index = int(cell_directories[-1][5:]) + 1
    else:
        cell_index = 1
    cell_string = "Cell_" + str(cell_index).zfill(3)

    save_directory = os.path.join(save_directory, cell_string)
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    if verbose:
        print("Data Will be Saved To:", save_directory)

    # Update the Model
    saving_settings['save_directory'] = save_directory
    saving_settings['date'] = date_string

    return save_directory

def save_yaml_file(file_directory, experiment, filename='experiment.yml'):
    try:
        file_name = os.path.join(file_directory, filename)
        with open(file_name, 'w') as f:
            f.write(experiment)
    except:
        return False
    return True

def update_from_channels_tab_controller(self):
    # get settings from channels tab
    settings = self.channels_tab_controller.get_values()

    # if there is something wrong, it will popup a window and return false
    for k in settings:
        if not settings[k]:
            tkinter.messagebox.showerror(title='Warning', message='There are some missing/wrong settings!')
            return False

    # validate channels
    try:
        for k in settings['channel']:
            float(settings['channel'][k]['laser_power'])
            float(settings['channel'][k]['interval_time'])
            if settings['channel'][k]['laser_index'] < 0 or settings['channel'][k]['filter_position'] < 0:
                raise
    except:
        tkinter.messagebox.showerror(title='Warning', message='There are some missing/wrong settings!')
        return False

    self.experiment.MicroscopeState['stack_cycling_mode'] = settings['stack_cycling_mode']
    for k in settings['stack_acquisition']:
        self.experiment.MicroscopeState[k] = settings['stack_acquisition'][k]
    for k in settings['timepoint']:
        self.experiment.MicroscopeState[k] = settings['timepoint'][k]

    # channels
    self.experiment.MicroscopeState['channels'] = settings['channel']

    # get all positions
    self.experiment.MicroscopeState['stage_positions'] = self.channels_tab_controller.get_positions()

    # get position information from stage tab
    position = self.stage_gui_controller.get_position()

    # validate positions
    if not position:
        tkinter.messagebox.showerror(title='Warning', message='There are some missing/wrong settings!')
        return False

    for axis in position:
        self.experiment.StageParameters[axis] = position[axis]
    step_size = self.stage_gui_controller.get_step_size()
    for axis in step_size:
        self.experiment.StageParameters[axis + '_step'] = step_size[axis]

def update_from_camera_setting_controller(self):
    self.experiment.CameraParameters['sensor_mode'] = self.camera_setting_controller.sensor_mode
    self.experiment.CameraParameters['binning'] = 1
    self.experiment.CameraParameters['x_pixels'] = self.camera_setting_controller.roi_widgets['Pixels_X'].get()
    self.experiment.CameraParameters['y_pixels'] = self.camera_setting_controller.roi_widgets['Pixels_Y'].get()
    self.experiment.CameraParameters['number_of_cameras'] = 1
