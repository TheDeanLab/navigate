# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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
import argparse
from pathlib import Path

# Third Party Imports

# Local Imports
from aslm.tools.main_functions import identify_gpu, add_parser_input_arguments
from aslm.config.config import get_aslm_path
class TestMain(unittest.TestCase):
    r"""Unit Test for main.py"""
    def test_identify_gpu(self):
        parser = argparse.ArgumentParser()
        parser = add_parser_input_arguments(parser)
        args = parser.parse_args(['--CPU'])
        args.CPU = True
        use_gpu = identify_gpu(args)
        assert use_gpu is not args.CPU

    def test_argument_parser(self):
        parser = argparse.ArgumentParser()
        parser = add_parser_input_arguments(parser)

        # Boolean arguments
        input_arguments = ['-sh',
                           '--synthetic_hardware',
                           '-d',
                           '--debug',
                           '--CPU']
        for arg in input_arguments:
            args = parser.parse_args([arg])
            pass

        # Path Arguments.
        aslm_path = Path(get_aslm_path())
        input_arguments = ['--config_file',
                           '--experiment_file',
                           '--etl_const_file',
                           '--rest_api_file',
                           '--logging_config']
        for arg in input_arguments:
            #  TODO: Figure out why this is throwing an error.
            #  args = parser.parse_args([arg], Path.joinpath(aslm_path, 'test.yml'))
            pass


if __name__ == '__main__':
    unittest.main()