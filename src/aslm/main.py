"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

"""
# Standard Library Imports
import argparse
from pathlib import Path
import tkinter as tk
import platform
from aslm.log_files.log_functions import log_setup

# Third Party Imports
import pretty_errors

# Local Imports
from aslm.controller.aslm_controller import ASLM_controller as controller


def main():
    r"""Multiscale ASLM Microscope Software.
    Microscope control software built in a Model-View-Controller architecture.
    Provides control of cameras, data acquisition cards, filter wheels, lasers
    stages, voice coils, and zoom servos.

    Parameters
    ----------
    *args : iterable
        --verbose
        --synthetic_hardware
        --sh
        --debug
        --CPU
        --config_file
        --experiment_file
        --etl_const_file
        --logging_config

    Examples
    --------
    python main.py --synthetic_hardware
    """

    # Specify the Default Configuration File Directories (located in src/config)
    base_directory = Path(__file__).resolve().parent
    configuration_directory = Path.joinpath(base_directory, 'config')

    # Full file paths.
    configuration_path = Path.joinpath(configuration_directory, 'configuration.yml')
    experiment_path = Path.joinpath(configuration_directory, 'experiment.yml')
    etl_constants_path = Path.joinpath(configuration_directory, 'etl_constants.yml')

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Multiscale Microscope Command Line Arguments')
    input_args = parser.add_argument_group('Input Arguments')
    input_args.add_argument('-v', '--verbose',
                            required=False,
                            default=False,
                            action='store_true',
                            help='Enables the software to operate in a verbose mode.  Warning: Excessively verbose.')

    input_args.add_argument('-sh', '--synthetic_hardware',
                            required=False,
                            default=False,
                            action='store_true',
                            help='Synthetic Hardware - '
                                 'Allows launching of the software without the physical devices attached.')

    input_args.add_argument('-d', '--debug',
                            required=False,
                            default=False,
                            action='store_true',
                            help='Enables debugging tool menu to be accessible.')

    input_args.add_argument('--CPU',
                            required=False,
                            default=False,
                            action='store_true',
                            help='Forces software to use CPU for analytical operations.  '
                                 'Overrides the automatic selection of a CUDA GPU if it is present by TensorFlow.')

    # Non-Default Configuration and Experiment Input Arguments
    input_args.add_argument('--config_file',
                            type=Path,
                            required=False,
                            default=None,
                            help='Non-default path to the configuration.yml file.  \n'
                                 'This file sets the default global physical'
                                 'state of the microscope.  For example, number of lasers, number of cameras, '
                                 'digital I/O, analog I/O, etc.')

    input_args.add_argument('--experiment_file',
                            type=Path,
                            required=False,
                            default=None,
                            help='Non-default path to the experiment.yml file. \n'
                                 'This file sets the default user-specified '
                                 'physical state of the microscope. For example, how many channels, '
                                 'and what are their exposure time, filter position, laser, etc. ')

    input_args.add_argument('--etl_const_file',
                            type=Path,
                            required=False,
                            default=None,
                            help='Non-default path to the etl_constants.yml file.  \n'
                                 'This file specifies the wavelength- and zoom-specific amplitude and offset '
                                 'of the ETL waveform generation.')

    input_args.add_argument('--logging_config',
                            type=Path,
                            required=False,
                            default=None,
                            help='Non-default path to the logging.yml config file \n'
                                 'This file specifies how the logging will be performed.')

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

    log_setup('logging.yml')

    # Evaluate GPU Status for Analysis Routines
    use_gpu = False
    if args.CPU:
        # If user overrides GPU search, keep use_gpu flag as False.
        pass
    else:
        if platform.system() != 'Darwin':
            import tensorflow as tf
            number_GPUs = len(tf.config.list_physical_devices('GPU'))
            if number_GPUs > 0:
                use_gpu = True

    # Start the GUI
    root = tk.Tk()
    controller(root,
               configuration_path,
               experiment_path,
               etl_constants_path,
               use_gpu,
               args)
    root.mainloop()


if __name__ == '__main__':
    if platform.system() == 'Darwin':
        print("Apple OS Not Fully Supported. ",
              "Tensorflow and CuPy based analysis is not possible. ",
              "Please try Linux or Windows for this functionality")

    main()

