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
import logging
import logging.config
import logging.handlers
import multiprocessing as mp
from pathlib import Path
import os
from datetime import datetime, timedelta
import shutil
from typing import Optional, Union
import json

# Third Party Imports
import yaml

# Local Imports
from navigate.config.config import get_navigate_path
from navigate.tools.common_dict_tools import update_nested_dict


# Custom performance logging level
PERFORMANCE = 25
logging.addLevelName(PERFORMANCE, "PERFORMANCE")


# Add a performance method to the Logger class
def performance(self, message, *args, **kwargs) -> None:
    """Log 'performance' messages at the PERFORMANCE level."""
    if self.isEnabledFor(PERFORMANCE):
        self._log(PERFORMANCE, message, args, **kwargs)


# Attach the performance method to the Logger class
logging.Logger.performance = performance


def find_filename(k: str, v: str) -> bool:
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


def log_setup(
    logging_configuration: str,
    logging_path: Optional[str] = None,
    queue=None,
    start_listener=False,
) -> Optional[Union[mp.Queue, tuple[mp.Queue, logging.handlers.QueueListener]]]:
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
    queue : multiprocessing.Queue, optional
        Queue to use for logging from sub-processes. If None, a new queue will be
        created if start_listener is True. Defaults to None.
    start_listener : bool, optional
        Whether to start a listener for the queue. Defaults to False.

    Returns
    -------
    Optional[Union[mp.Queue, tuple[mp.Queue, logging.handlers.QueueListener]]]
        If start_listener is True, returns a tuple containing the queue and the listener.
        If start_listener is False and a queue is provided, returns the queue.
        Otherwise, returns None.
    """

    # path to logging_configuration is set relative
    # to the location of the folder containing this file (log_functions.py)
    base_directory = Path(__file__).resolve().parent
    logging_configuration_path = Path.joinpath(base_directory, logging_configuration)

    # Save directory for logging information.
    time: datetime = datetime.now()
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

    current_path = Path.joinpath(logging_path, time_stamp)
    if not os.path.exists(current_path):
        os.mkdir(current_path)

    # Discard log files older than 30 days
    eliminate_old_log_files(logging_path)

    def update_filename(v: str) -> str:
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
        return Path.joinpath(current_path, v)

    # Read the logging configuration file.
    with open(logging_configuration_path, "r") as f:
        try:
            config_data = yaml.load(f.read(), Loader=yaml.FullLoader)

            # Force all log files to be created relative to logging_path
            config_data2 = update_nested_dict(
                config_data, find_filename, update_filename
            )
            # Configures our loggers from updated logging.yml
            logging.config.dictConfig(config_data2)

        except yaml.YAMLError as yaml_error:
            print(yaml_error)

    # If a queue is provided, or we are to start a listener,
    if queue is None and start_listener:
        queue = mp.Queue(-1)

    if queue:
        qh = logging.handlers.QueueHandler(queue)
        handlers = []
        for name in [""] + list(config_data2.get("loggers", {})):
            logger = logging.getLogger(name or None)
            for handler in logger.handlers:
                if handler not in handlers:
                    handlers.append(handler)
            logger.handlers = [qh]
        if start_listener:
            listener = logging.handlers.QueueListener(
                queue, *handlers, respect_handler_level=True
            )
            listener.start()
            return queue, listener
        return queue
    return None


def eliminate_old_log_files(logging_path: str) -> None:
    """Eliminate log files in the logging folder older than 30 days.

    Parameters
    ----------
    logging_path : str
        Path to logs files.
    """

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


def load_latest_log_file() -> tuple:
    """Load the latest log file from the logging directory.

    Returns
    -------
    tuple
        Tuple containing the model log data and controller log data.
    """

    date_dirs = []
    logging_path = Path.joinpath(Path(get_navigate_path()), "logs")

    # Iterate through all folders in logging path
    for folder in os.listdir(logging_path):
        date = get_folder_date(folder)
        if date is not False:
            date_dirs.append(folder)

    # Sort the directories by date
    latest_dir = max(date_dirs)

    controller_log_path = os.path.join(
        logging_path, latest_dir, "view_controller_debug.log"
    )
    model_log_path = os.path.join(logging_path, latest_dir, "model_debug.log")
    performance_log_path = os.path.join(logging_path, latest_dir, "performance.log")

    # Default to None if the log files do not exist
    controller_log_data = None
    model_log_data = None
    performance_log_data = None

    try:
        if controller_log_path and os.path.exists(controller_log_path):
            with open(controller_log_path, "r") as file:
                controller_log_data = file.readlines()
    except Exception:
        pass

    try:
        if model_log_path and os.path.exists(model_log_path):
            with open(model_log_path, "r") as file:
                model_log_data = file.readlines()
    except Exception:
        pass

    try:
        if performance_log_path and os.path.exists(performance_log_path):
            performance_log_data = []
            with open(performance_log_path, "r") as file:
                for line in file:
                    try:
                        performance_log_data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass

    return model_log_data, controller_log_data, performance_log_data


def get_folder_date(folder_name: str) -> datetime:
    """Get the date from the log folder's name.

    Parameters
    ----------
    folder_name : str
        Folder name in the format 'YYYY-MM-DD-HHMM'.

    Returns : datetime or bool
        Returns a datetime object if the folder name is in the correct format.
        The format is 'YYYY-MM-DD-HHMM', where:
            - YYYY: 4-digit year
            - MM: 2-digit month (01-12)
            - DD: 2-digit day (01-31)
            - HHMM: 4-digit hour and minute (HHMM, e.g., 1530 for 3:30 PM)
        If the folder name is not in this format, it will return False.
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
        return False
