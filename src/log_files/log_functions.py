import logging
import logging.handlers
import multiprocessing
import yaml
from pathlib import Path


def log_setup(fname):
    base_directory = Path(__file__).resolve().parent
    print(base_directory)
    logging_path = Path.joinpath(base_directory, fname)
    print(logging_path)
    with open(logging_path, 'r') as f:
        try:
            config_data = yaml.load(f.read(), Loader=yaml.FullLoader)
            logging.config.dictConfig(config_data)  # Configures our loggers from logging.yml
        except yaml.YAMLError as yaml_error:
            print(yaml_error)


def main_process_listener(queue):
    '''
    This function will listen for new logs put in queue from sub processes, it will then log via the main process.
    '''
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