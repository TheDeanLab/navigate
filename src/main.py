"""
Starting point for running the program.
"""
# Standard Library Imports
import os
import argparse
from pathlib import Path
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

    # Configuration and Experiment input arguments
    input_args.add_argument('--config_file', type=Path, required=False, default=None, help='path to configuration.yml file')
    input_args.add_argument('--experiment_file', type=Path, required=False, default=None, help='path to experiment.yml file')
    input_args.add_argument('--etl_const_file', type=Path, required=False, default=None, help='path to etl_constants.yml file')

    #TODO: Add path to experiment file if user wants to load previous settings.
    args = parser.parse_args()

    # Specify the Default Configuration Files (located in src/config)
    base_directory = Path(os.path.dirname(os.path.abspath(__file__)))
    configuration_directory = Path(os.path.join(base_directory, 'config'))
    configuration_path = Path(os.path.join(configuration_directory, 'configuration.yml'))
    experiment_path = Path(os.path.join(configuration_directory, 'experiment.yml'))
    etl_constants_path = Path(os.path.join(configuration_directory, 'etl_constants.yml'))

    if args.config_file is not None:
       #TODO: #TODO: Possibly make sub-routine to check properties of file before launching
       assert args.config_file.exists(), "Configuration file Path {} not valid".format(args.config_file)
       configuration_path = args.config_file
    if args.experiment_file is not None:
        #TODO: #TODO: Possibly make sub-routine to check properties of file before launching
        assert args.experiment_file.exists(), "experiment_file file Path {} not valid".format(args.experiment_file)
        experiment_path = args.experiment_file
    if args.etl_const_file is not None:
        #TODO: Possibly make sub-routine to check properties of file before launching
        assert args.etl_const_file.exists(), "etl_const_file Path {} not valid".format(args.etl_const_file)
        etl_constants_path = args.etl_const_file

    # Start the GUI
    root = tk.Tk()
    app = controller(root, configuration_path, experiment_path, etl_constants_path, args)
    root.mainloop()

if __name__ == '__main__':
    main()

