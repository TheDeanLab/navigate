# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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

import logging.config
import logging.handlers
from pathlib import Path
import os

import yaml


def update_nested_dict(d, find_func, apply_func):
    """
    Loops through a nested dictionary and if find_func() conditions are met,
    run apply_func on that key.

    TODO: This is highly general and doesn't belong here.
    TODO: It might be nice to make this non-recursive.

    Parameters
    ----------
    find_func : func
        Accepts key, value pair and matches a condition based on these. Returns bool.
    apply_func : func
        Accepts a value returns the new value.

    Returns
    -------
    d2 : dict
        An version of d, updated according to the passed functions.
    """
    d2 = {}
    for k, v in d.items():
        if find_func(k, v):
            d2[k] = apply_func(v)
        else:
            d2[k] = v
        if isinstance(v, dict):
            d2[k] = update_nested_dict(v, find_func, apply_func)
    return d2


def find_filename(k, v):
    """
    Check that we've met the condition dictionary key == 'filename'
    """
    if k == "filename":
        return True
    return False


def log_setup(fname):
    """
    Initialize a logger from a YAML file containing information in the Python logging
    dictionary format
    (see https://docs.python.org/3/library/logging.config.html#logging-config-dictschema).

    Parameters
    ----------
    fname : str
        Path to file to be loaded. Relative to the location of the folder containing this file.
    """

    # the path to fname is set relative to the location of the folder containing this file (log_functions.py)
    base_directory = Path(__file__).resolve().parent
    config_path = Path.joinpath(base_directory, fname)

    logging_path = Path.joinpath(base_directory, "LOGS")
    if not os.path.exists(logging_path):
        os.mkdir(logging_path)

    # Function to map filename to base_directory/filename in the dictionary
    def update_filename(v):
        return Path.joinpath(base_directory, v)

    with open(config_path, "r") as f:
        try:
            config_data = yaml.load(f.read(), Loader=yaml.FullLoader)
            # Force all log files to be created relative to base_directory
            config_data2 = update_nested_dict(
                config_data, find_filename, update_filename
            )
            logging.config.dictConfig(
                config_data2
            )  # Configures our loggers from updated logging.yml
        except yaml.YAMLError as yaml_error:
            print(yaml_error)


def main_process_listener(queue):
    """
    This function will listen for new logs put in queue from sub processes, it will then log via the main process.
    """
    while True:
        try:
            record = queue.get()
            if record is None:  # Sentinel to tell listener to stop
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import sys, traceback

            print("Whoops! Problem: ", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
