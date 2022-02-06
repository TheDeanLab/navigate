# Standard library imports
from datetime import datetime
import os

# Third party imports


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
    save_directory = os.path.join(saving_settings['root_directory'], user_string, tissue_string,
                                  celltype_string, label_string, date_string)
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Determine Number of Cells in Directory
    cell_directories = list(filter(lambda v: v[:5] == 'Cell-', os.listdir(save_directory)))
    if cell_directories:
        cell_directories.sort()
        cell_index = int(cell_directories[-1][5:]) + 1
    else:
        cell_index = 0
    cell_string = "Cell-" + str(cell_index).zfill(6)

    save_directory = os.path.join(save_directory, cell_string)
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
    if verbose:
        print("Data Will be Saved To:", save_directory)

    # Update the Model
    saving_settings['save_directory'] = save_directory
    saving_settings['date'] = date_string

    return save_directory


def save_experiment_file(file_directory, experiment, filename='experiment.yml'):
    try:
        file_name = os.path.join(file_directory, filename)
        with open(file_name, 'w') as f:
            f.write(experiment)
    except:
        return False
    return True
    