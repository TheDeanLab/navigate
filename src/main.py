"""
Starting point for running the program.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

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
import platform
import logging
import logging.config
import yaml


# Third Party Imports
import tensorflow as tf

# Local Imports
from controller.aslm_controller import ASLM_controller as controller


def main():
    # Evaluate GPU Status for Analysis Routines
    number_GPUs = len(tf.config.list_physical_devices('GPU'))
    if number_GPUs == 0:
        USE_GPU = False
        print('No NVIDIA GPU in system. Running on CPU only.')
    else:
        USE_GPU = True
        print('NVIDIA GPU detected.')

    # Specify the Default Configuration File Directories (located in src/config)
    base_directory = Path(__file__).resolve().parent
    configuration_directory = Path.joinpath(base_directory, 'config')
    logging_directory = Path.joinpath(base_directory, 'log_files')

    # Full file paths.
    configuration_path = Path.joinpath(configuration_directory, 'configuration.yml')
    experiment_path = Path.joinpath(configuration_directory, 'experiment.yml')
    etl_constants_path = Path.joinpath(configuration_directory, 'etl_constants.yml')
    logging_path = Path.joinpath(logging_directory, 'logging.yml')

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Microscope Control Arguments')
    input_args = parser.add_argument_group('Input Arguments')
    input_args.add_argument('--verbose',
                            required=False,
                            default=False,
                            action='store_true',
                            help='Verbose output')

    input_args.add_argument('--synthetic_hardware',
                            required=False,
                            default=False,
                            action='store_true',
                            help='Synthetic hardware modules')

    input_args.add_argument('--sh',
                            required=False,
                            default=False,
                            action='store_true',
                            help='Synthetic hardware modules')

    input_args.add_argument('--debug',
                            required=False,
                            default=False,
                            action='store_true',
                            help='Debugging tools')

    # Non-Default Configuration and Experiment Input Arguments
    input_args.add_argument('--config_file',
                            type=Path,
                            required=False,
                            default=None,
                            help='path to configuration.yml file')

    input_args.add_argument('--experiment_file',
                            type=Path,
                            required=False,
                            default=None,
                            help='path to experiment.yml file')

    input_args.add_argument('--etl_const_file',
                            type=Path,
                            required=False,
                            default=None,
                            help='path to etl_constants.yml file')

    input_args.add_argument('--logging_config',
                            type=Path,
                            required=False,
                            default=None,
                            help='path to logging.yml config file')

    #  Parse Arguments
    args = parser.parse_args()

    # If non-default configuration, experiment, or ETL constant file is provided as an input argument.
    # TODO: Possibly make sub-routine to check properties of file before loading.
    if args.config_file:
        assert args.config_file.exists(), "Configuration file Path {} not valid".format(args.config_file)
        configuration_path = args.config_file

    if args.experiment_file:
        assert args.experiment_file.exists(), "experiment_file file Path {} not valid".format(args.experiment_file)
        experiment_path = args.experiment_file

    if args.etl_const_file:
        assert args.etl_const_file.exists(), "etl_const_file Path {} not valid".format(args.etl_const_file)
        etl_constants_path = args.etl_const_file

    # Creating Loggers etc., they exist globally so no need to pass
    if args.logging_config:
        assert args.logging_config.exists(), "Logging Config Path {} not valid".format(args.logging_config)
        logging_path = args.logging_config

    with open(logging_path, 'r') as f:
        try:
            config_data = yaml.load(f.read(), Loader=yaml.FullLoader)
            logging.config.dictConfig(config_data)  # Configures our loggers from logging.yml
        except yaml.YAMLError as yaml_error:
            print(yaml_error)

    # Start the GUI
    root = tk.Tk()
    controller(root, configuration_path, experiment_path, etl_constants_path, USE_GPU, args)
    root.mainloop()


if __name__ == '__main__':
    if platform.system() == 'Darwin':
        print("Apple OS Not Fully Supported. ",
              "Tensorflow and CuPy based analysis is not possible. ",
              "Please try Linux or Windows for this functionality")

    main()

