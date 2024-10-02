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


# Standard library imports
from datetime import datetime
import os
import json
import yaml
from pathlib import Path
import psutil
from typing import Union
import logging

# Third party imports

# Local application imports
from navigate.tools.common_functions import copy_proxy_object

# Logger setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


def get_ram_info() -> tuple:
    """Get computer RAM information.

    This function retrieves the total and available RAM on the computer.

    Note
    ----
    This function uses the psutil library to retrieve the RAM information.
    The returned value is in bytes. To convert to GB, divide by 1024^3.

    Returns
    -------
    total_ram : int
        Total RAM on the computer.
    available_ram : int
        Available RAM on the computer.
    """
    virtual_memory = psutil.virtual_memory()
    total_ram = virtual_memory.total
    available_ram = virtual_memory.available
    return total_ram, available_ram


def create_save_path(saving_settings: dict) -> str:
    """Create path to save the data to.

    This function retrieves the user inputs from the popup save window.
    It then creates a new directory in the user specified path.

    Parameters
    ----------
    saving_settings : dict
        Dictionary containing information necessary to build path to save data to.

    Returns
    -------
    save_directory : str
        Path to save data to.
    """
    root_directory = saving_settings["root_directory"]
    user_string = saving_settings["user"]
    tissue_string = saving_settings["tissue"]
    cell_type_string = saving_settings["celltype"]
    label_string = saving_settings["label"]
    prefix_string = saving_settings["prefix"]
    date_string = str(datetime.now().date())

    # Make sure that there are no spaces in the variables
    user_string = user_string.replace(" ", "-")
    tissue_string = tissue_string.replace(" ", "-")
    cell_type_string = cell_type_string.replace(" ", "-")
    label_string = label_string.replace(" ", "-")

    # Create the save directory on disk.
    save_directory = os.path.join(
        root_directory,
        user_string,
        tissue_string,
        cell_type_string,
        label_string,
        date_string,
    )

    os.makedirs(save_directory, exist_ok=True)
    # Determine Number of Cells in Directory
    # Cell1/Position1/1_CH00_000000.tif
    prefix_num = len(prefix_string)
    cell_directories = list(
        filter(lambda v: v[:prefix_num] == prefix_string, os.listdir(save_directory))
    )
    if len(cell_directories) != 0:
        cell_directories.sort()
        cell_index = int(cell_directories[-1][prefix_num:]) + 1
    else:
        cell_index = 1
    # cell_string = "Cell_" + str(cell_index).zfill(3)
    cell_string = prefix_string + str(cell_index).zfill(3)

    save_directory = os.path.join(save_directory, cell_string)
    os.makedirs(save_directory, exist_ok=True)

    # Update the experiment dict
    saving_settings["save_directory"] = save_directory
    saving_settings["date"] = date_string

    return save_directory


def load_yaml_file(file_path: str) -> Union[dict, None]:
    """Load YAML file from Disk

    Parameters
    ----------
    file_path : str/os.path
        String or path of the yaml file.

    Returns
    -------
    config_data: dict/None
        A dictionary of the yaml file content.
        None: if the yaml file has error or not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    with open(file_path) as f:
        try:
            config_data = yaml.load(f, Loader=yaml.FullLoader)
        except yaml.YAMLError as yaml_error:
            error_statement = f"Can't load yaml file: {file_path} - {yaml_error}"
            logger.debug(error_statement)
            print(error_statement)
            return None
    return config_data


def save_yaml_file(
    file_directory: str, content_dict: dict, filename="experiment.yml"
) -> bool:
    """Same YAML file to Disk

    Parameters
    ----------
    file_directory : str
        String of directory to save data to.
    content_dict : dict
        Dictionary that holds information about specified content.
    filename : str
        String of name to save data to.  Default is experiment.yml.

    Returns
    -------
    bool
        True if file was saved successfully, False otherwise.
    """
    if file_directory != "" and not os.path.exists(file_directory):
        return False

    try:
        file_name = os.path.join(file_directory, filename)
        if os.path.exists(file_name):
            with open(file_name, "r") as f:
                file_content = f.read()
        else:
            file_content = ""
        with open(file_name, "w") as f:
            f.write(json.dumps(copy_proxy_object(content_dict), indent=4))
    except BaseException:
        with open(file_name, "w") as f:
            f.write(file_content)
        return False
    return True


def delete_folder(top: str) -> None:
    """Delete folder and all sub-folders.

    https://docs.python.org/3/library/os.html#os.walk

    Delete everything reachable from the directory named in "top",
    assuming there are no symbolic links.
    CAUTION:  This is dangerous!  For example, if top == '/', it
    could delete all your disk files.

    Parameters
    ----------
    top : str
        Path to folder to delete.
    """
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
            except PermissionError:
                # Windows locks these files sometimes
                pass
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except OSError:
                # One of the directories containing a file Windows decided to lock
                pass

    try:
        os.rmdir(top)
    except OSError:
        pass
