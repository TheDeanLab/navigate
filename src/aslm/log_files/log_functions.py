from email.mime import base
import logging.config
import logging.handlers
import yaml
from pathlib import Path

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
    if k == 'filename':
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
    logging_path = Path.joinpath(base_directory, fname)

    # Function to map filename to base_directory/filename in the dictionary
    def update_filename(v):
        return Path.joinpath(base_directory, v)

    with open(logging_path, 'r') as f:
        try:
            config_data = yaml.load(f.read(), Loader=yaml.FullLoader)
            # Force all log files to be created relative to base_directory
            config_data2 = update_nested_dict(config_data, find_filename, update_filename)
            logging.config.dictConfig(config_data2)  # Configures our loggers from updated logging.yml
        except yaml.YAMLError as yaml_error:
            print(yaml_error)

def main_process_listener(queue):
    """
    This function will listen for new logs put in queue from sub processes, it will then log via the main process.
    """
    while True:
        try:
            record = queue.get()
            if record is None: # Sentinel to tell listener to stop
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import sys, traceback
            print("Whoops! Problem: ", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
