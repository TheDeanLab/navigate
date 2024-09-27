# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

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
import logging.config
import logging.handlers
from pathlib import Path
import os
import sys
import traceback
from datetime import datetime, timedelta
import shutil

# Third Party Imports
import yaml

# Local Imports
from navigate.config.config import get_navigate_path
from navigate.tools.common_dict_tools import update_nested_dict


def find_filename(k, v):
    """Check that we've met the condition dictionary key == 'filename'

    Parameters
    ----------
    k : str
        Dictionary key
    v : str
        Dictionary value

    Returns
    -------
    bool
        True if k == 'filename', False otherwise
    """
    if k == "filename":
        return True
    return False


def log_setup(logging_configuration, logging_path=None):
    """Setup logging configuration

    Initialize a logger from a YAML file containing information in the Python logging
    dictionary format.

    Note
    ----
        Additional information here:
        https://docs.python.org/3/library/logging.config.html#logging-config-dictschema

    Parameters
    ----------
    logging_configuration : str
        Path to file to be loaded.
        Relative to the location of the folder containing this file.
    logging_path : str, optional
        Path to store logs. Defaults to navigate_path/logs
    """

    # path to logging_configuration is set relative
    # to the location of the folder containing this file (log_functions.py)
    base_directory = Path(__file__).resolve().parent
    logging_configuration_path = Path.joinpath(base_directory, logging_configuration)

    # Save directory for logging information.
    time = datetime.now()
    time_stamp = Path(
        "%s-%s-%s-%s%s"
        % (
            f"{time.year:04d}",
            f"{time.month:02d}",
            f"{time.day:02d}",
            f"{time.hour:02d}",
            f"{time.minute:02d}",
        )
    )

    if logging_path is None:
        logging_path = Path.joinpath(Path(get_navigate_path()), "logs")

    if not os.path.exists(logging_path):
        os.mkdir(logging_path)

    todays_path = Path.joinpath(logging_path, time_stamp)
    if not os.path.exists(todays_path):
        os.mkdir(todays_path)

    # Discard log files older than 30 days
    eliminate_old_log_files(logging_path)

    def update_filename(v):
        """Function to map filename to base_directory/filename in the dictionary

        Parameters
        ----------
        v : str
            Value to be updated

        Returns
        -------
        Path : str
            Path to the log file
        """
        return Path.joinpath(todays_path, v)

    # Read the logging configuration file.
    with open(logging_configuration_path, "r") as f:
        try:
            config_data = yaml.load(f.read(), Loader=yaml.FullLoader)

            # Force all log files to be created relative to logging_path
            config_data2 = update_nested_dict(
                config_data, find_filename, update_filename
            )
            logging.config.dictConfig(config_data2)

            # Configures our loggers from updated logging.yml
        except yaml.YAMLError as yaml_error:
            print(yaml_error)


def eliminate_old_log_files(logging_path):
    """Eliminate log files in the logging folder older than 30 days.

    Parameters
    ----------
    logging_path : str
        Path to logs files.
    """

    def get_folder_date(folder_name):
        """Get the date from the folder name.

        Parameters
        ----------
        folder_name : str
            Folder name
        """
        try:
            # Extract the year, month, day, hour, and minute from the folder name
            year, month, day, hourminute = folder_name.split("-")
            hour = hourminute[:2]
            minute = hourminute[2:]
            date = datetime(
                year=int(year),
                month=int(month),
                day=int(day),
                hour=int(hour),
                minute=int(minute),
            )
            return date
        except ValueError:
            # Folder name is not in anticipated format
            return False

    today = datetime.now()
    date_threshold = today - timedelta(days=30)

    # Iterate through all folders in logging path and delete those older than 30 days
    for folder in os.listdir(logging_path):
        folder_date = get_folder_date(folder)
        if folder_date is not False:
            if folder_date < date_threshold:
                old_path = Path.joinpath(logging_path, folder)
                try:
                    shutil.rmtree(old_path)
                except OSError:
                    continue


def main_process_listener(queue):
    """Listener function for the main process

    This function will listen for new logs put in queue from sub processes,
    it will then log via the main process.

    Parameters
    ----------
    queue : multiprocessing.Queue
        Queue to listen for new logs
    """
    while True:
        try:
            record = queue.get()
            if record is None:
                # Sentinel to tell listener to stop
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            print("Whoops! Problem: ", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
