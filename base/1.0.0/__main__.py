"""
Starting point for running the program.
"""
# Standard Library Imports
import os
import argparse
import tkinter as tk

# Third Party Imports
import pretty_errors

# Local Imports
from controller.aslm_controller import ASLM_controller as controller

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Microscope Control Arguments')
    input_args = parser.add_argument_group('Input Arguments')
    input_args.add_argument('--verbose', required=False, default=False, action='store_true', help='Verbose output')
    input_args.add_argument('--synthetic_hardware', required=False, default=False, action='store_true', help='Synthetic hardware modules')
    #TODO: Add path to experiment file if user wants to load previous settings.
    args = parser.parse_args()

    # Specify the Configuration Directory
    base_directory = os.path.dirname(os.path.abspath(__file__))
    configuration_directory = os.path.join(base_directory, 'config')
    configuration_path = os.path.join(configuration_directory, 'configuration.yml')
    experiment_path = os.path.join(configuration_directory, 'experiment.yml')

    # Start the GUI
    root = tk.Tk()
    app = controller(root, configuration_path, experiment_path, args)
    root.mainloop()

if __name__ == '__main__':
    main()

