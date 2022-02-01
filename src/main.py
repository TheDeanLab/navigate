"""
Starting point for running the program.

ASLM software modified code and/or took inspiration from a number of sources with different licenses.
Listed here for bookkeeping purposes.

https://github.com/uetke/UUTrack    - GNU GPL v3.0      - Architecture, camera.
https://github.com/mesoSPIM/mesoSPIM-control    - GNU GPL v3.0
https://github.com/MicroscopeAutoPilot/autopilot    - NPOSL-3.0
https://github.com/bicarlsen/obis_laser_controller  - GNU GPL v3.0  - Laser Controller
https://github.com/AndrewGYork/tools - GNU GPL v2.0 - Sutter Filter Wheel
"""
# Standard Library Imports
import argparse
from pathlib import Path
import tkinter as tk

# Third Party Imports

# Local Imports
from controller.aslm_controller import ASLM_controller as controller


def main():
    # Specify the Default Configuration Files (located in src/config)
    base_directory = Path(__file__).resolve().parent
    configuration_directory = Path.joinpath(base_directory, 'config')
    configuration_path = Path.joinpath(configuration_directory, 'configuration.yml')
    experiment_path = Path.joinpath(configuration_directory, 'experiment.yml')
    etl_constants_path = Path.joinpath(configuration_directory, 'etl_constants.yml')

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Microscope Control Arguments')
    input_args = parser.add_argument_group('Input Arguments')
    input_args.add_argument('--verbose', required=False, default=False, action='store_true', help='Verbose output')
    input_args.add_argument('--synthetic_hardware', required=False, default=False, action='store_true',
                            help='Synthetic hardware modules')

    # Configuration and Experiment input arguments
    input_args.add_argument('--config_file', type=Path, required=False, default=None,
                            help='path to configuration.yml file')
    input_args.add_argument('--experiment_file', type=Path, required=False, default=None,
                            help='path to experiment.yml file')
    input_args.add_argument('--etl_const_file', type=Path, required=False, default=None,
                            help='path to etl_constants.yml file')

    args = parser.parse_args()

    if args.config_file:
        # TODO: Possibly make sub-routine to check properties of file before launching
        assert args.config_file.exists(), "Configuration file Path {} not valid".format(args.config_file)
        configuration_path = args.config_file
    if args.experiment_file:
        assert args.experiment_file.exists(), "experiment_file file Path {} not valid".format(args.experiment_file)
        experiment_path = args.experiment_file
    if args.etl_const_file:
        assert args.etl_const_file.exists(), "etl_const_file Path {} not valid".format(args.etl_const_file)
        etl_constants_path = args.etl_const_file

    # Start the GUI
    root = tk.Tk()
    app = controller(root, configuration_path, experiment_path, etl_constants_path, args)
    root.mainloop()


if __name__ == '__main__':
    main()
