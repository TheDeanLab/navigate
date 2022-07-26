"""
ASLM Model Configuration
Store variables that can be shared between different classes

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
"""

# Standard Imports
from __future__ import (absolute_import, division, print_function)
import sys
from pathlib import Path
import logging

# Third Party Imports
import yaml

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class Session:
    """Session Class

    Stores variables and other classes that are common to several UI or instances of the code.
    Custom dunder setattr and getattr methods are used to add functionality.  Previously emitted signals for pyQt.

    Parameters
    ----------
    file_path : Path
        Path instance of file path to the configuration or experiment yaml file.
    """

    def __init__(self,
                 file_path=None):
        """The class is prepared to load values from a Yaml file
        :param file: Path to the file where the config file is or a dictionary with the data to load.
        :arg args: Arguments passed to the program from the command line.
        """

        super(Session, self).__init__()
        super().__setattr__('params', dict())

        """
        Load a Yaml file and stores the values in the object.
        :param file: Path to the file where the config file is.
        """

        if file_path is None:
            print("No file provided to load_yaml_config()")
            logging.debug("No file path provided to load the configuration or experiment yaml file.")
            sys.exit(1)
        else:
            if isinstance(file_path, Path):
                assert file_path.exists(), 'Configuration File not found: {}'.format(file_path)
                with open(file_path) as f:
                    try:
                        config_data = yaml.load(f, Loader=yaml.FullLoader)
                    except yaml.YAMLError as yaml_error:
                        logging.debug(f"Session - Yaml Error: {yaml_error}")

        # Set the attributes with the custom __setattr__
        for data_iterator in config_data:
            self.__setattr__(data_iterator,
                             config_data[data_iterator])

    def __setattr__(self,
                    key,
                    value):
        """Custom setter for Configuration and Experiment attributes.

        Parameters
        ----------
        key : str
            name of the attribute, e.g. 'Devices'
        value : dict
            Dictioanry of attribute values, e.g., {'daq': 'NI', 'camera': 'HamamatsuOrca', 'etl': 'ETL', ...
        """
        # # Confirm that the value is a dictionary
        if not isinstance(value, dict):
            raise Exception('Everything passed to a the configuration must be a dictionary')

        # If the key does not exist in self.params, add it
        if key not in self.params:
            self.params[key] = dict()
            self.__setattr__(key, value)

        else:
            for k in value:
                if k in self.params[key]:
                    val = value[k]
                    self.params[key][k] = value[k]
                else:
                    self.params[key][k] = value[k]

            super(Session, self).__setattr__(k, value[k])

    def __getattr__(self, item):
        if item not in self.params:
            return None
        else:
            return self.params[item]

    def __str__(self):
        r"""Overrides the print(class).

        Returns
        -------
        s : str
            A Yaml-ready string.
        """

        s = ''
        for key in self.params:
            s += '%s:\n' % key
            for kkey in self.params[key]:
                s += '  %s: %s\n' % (kkey, self.params[key][kkey])
        return s

    def serialize(self):
        r"""Overrides the print(class).

        Function kept for compatibility.

        Returns
        -------
        string : str
            Yaml-ready string.
        """
        return self.__str__()

    # def copy(self):
    #     """
    #     Copies this class. Important not to overwrite the memory of a previously created .
    #     :return: a  exactly the same as this one.
    #     """
    #     return Session(self.params)

