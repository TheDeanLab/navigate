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

#  Standard Library Imports
import logging

# Third Party Imports

# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class FilterWheelBase:
    r"""FilterWheelBase Class

    Parent class for controlling filter wheels.

    Attributes
    ----------
    comport : str
        Comport for communicating with the filter wheel, e.g., COM1.
    baudrate : int
        Baud rate for communicating with the filter wheel, e.g., 9600.
    filter_dictionary : dict
        Dictionary with installed filter names, e.g., filter_dictionary = {'GFP', 0}.
    number_of_filter_wheels : int
        Number of installed filter wheels.
    wheel_position : int
        Default filter wheel position
    verbose : bool
        Verbosity
    wait_until_done_delay = float
        Duration of time to wait for a filter wheel change.
    wait_until_done = bool
        Flag for enabling the wait period for a filter wheel change.

    Methods
    -------
    check_if_filter_in_filter_dictionary()
        Checks to see if filter name exists in the filter dictionary.
    """

    def __init__(self, model, verbose):
        self.comport = model.FilterWheelParameters['filter_wheel_port']
        self.baudrate = model.FilterWheelParameters['baudrate']
        self.filter_dictionary = model.FilterWheelParameters['available_filters']
        self.number_of_filter_wheels = model.FilterWheelParameters['number_of_filter_wheels']
        self.wheel_position = 0
        self.verbose = verbose
        self.wait_until_done_delay = 0.03
        self.wait_until_done = True

    def check_if_filter_in_filter_dictionary(self, filter_name):
        r"""Checks if the filter designation (string) given exists in the filter dictionary

        Parameters
        ----------
        filter_name : str
            Name of filter.

        Returns
        -------
        filter_exists : bool
            Flag if filter exists in the filter dictionary.

        """
        if filter_name in self.filter_dictionary:
            filter_exists = True
        else:
            filter_exists = False
            logger.debug('Filter Name not in the Filter Dictionary')
            raise ValueError('Filter Name not in the Filter Dictionary.')
        return filter_exists


