# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

# Standard Library Imports
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Third Party Imports

# Local Imports
from navigate.tools.main_functions import create_parser
from navigate.config.config import get_navigate_path
from navigate.main import main


def get_args():
    args = MagicMock()
    args.configurator = False
    args.config_file = False
    args.experiment_file = False
    args.waveform_constants_file = False
    args.rest_api_file = False
    args.waveform_templates_file = False
    args.gui_config_file = False
    args.logging_config = False
    args.synthetic_hardware = True
    return args


class TestArgParser(unittest.TestCase):
    """Unit Test for main.py"""

    def test_argument_parser(self):
        """Test Argument Parser"""
        parser = create_parser()

        # Boolean arguments
        input_arguments = ["-sh", "--synthetic-hardware"]
        for arg in input_arguments:
            parser.parse_args([arg])

        # Path Arguments.
        navigate_path = Path(get_navigate_path())
        input_arguments = [
            "--config-file",
            "--experiment-file",
            "--waveform-constants-file",
            "--rest-api-file",
            "--logging-config",
            "--gui-config-file",
        ]
        for arg in input_arguments:
            parser.parse_args([arg, str(Path.joinpath(navigate_path, "test.yml"))])


class TestMainController(unittest.TestCase):
    """Unit Test for main.py"""

    @patch("navigate.main.tk.Tk.mainloop")
    @patch("navigate.main.Controller")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_call_controller(
        self, mock_parse_args, mock_controller, mock_mainloop
    ):
        args = get_args()
        mock_parse_args.return_value = args

        mock_mainloop.return_value = MagicMock()
        main()
        mock_controller.assert_called_once()


# class TestMainConfigurator(unittest.TestCase):
#     """ Unit Test for main.py """
#     @patch('navigate.main.tk.Tk.mainloop')
#     @patch('navigate.main.Controller')
#     @patch('argparse.ArgumentParser.parse_args')
#     def test_main_configurator(
#             self,
#             mock_parse_args,
#             mock_controller,
#             mock_mainloop
#     ):
#         args = get_args()
#         args.configurator = True
#         mock_parse_args.return_value = args
#
#         mock_mainloop.return_value = MagicMock()
#         main()
#         mock_controller.assert_not_called()
