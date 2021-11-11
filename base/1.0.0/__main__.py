"""   Starting point for running the program. """
# Import built-in modules
import os
from multiprocessing import Process

# Import local modules
from StartMonitor import start
from config import constants

if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    verbose = True
    if verbose:
        print("The Base Directory is:", BASE_DIR)

    # Start the monitor
    start(constants, verbose)
    if verbose:
        print("Launching the StartMonitor")