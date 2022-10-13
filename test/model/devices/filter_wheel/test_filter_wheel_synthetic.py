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
import unittest

# Third Party Imports
import pytest

from aslm.model.devices.filter_wheel.filter_wheel_synthetic import SyntheticFilterWheel
from aslm.model.dummy import DummyModel

class TestSyntheticFilterWheel(unittest.TestCase):
    r"""Unit Test for FilterWheel Class"""
    dummy_model = DummyModel()
    microscope_name = 'microscope_low_res'
    synthetic_filter = SyntheticFilterWheel(microscope_name, None, dummy_model.configuration)

    # def test_synthetic_filter_wheel_attributes(self):
    #     assert hasattr(self.synthetic_filter, 'comport')
    #     assert hasattr(self.synthetic_filter, 'baudrate')
    #     assert hasattr(self.synthetic_filter, 'filter_dictionary')
    #     assert hasattr(self.synthetic_filter, 'number_of_filter_wheels')
    #     assert hasattr(self.synthetic_filter, 'wait_until_done_delay')
    #     assert hasattr(self.synthetic_filter, 'wait_until_done')

    # def test_synthetic_filter_wheel_attributes_type(self):
    #     assert type(self.synthetic_filter.comport == str)
    #     assert type(self.synthetic_filter.baudrate == int)
    #     assert type(self.synthetic_filter.filter_dictionary == dict)
    #     assert type(self.synthetic_filter.number_of_filter_wheels == int)
    #     assert type(self.synthetic_filter.wheel_position == int)
    #     assert type(self.synthetic_filter.wait_until_done_delay == float)
    #     assert type(self.synthetic_filter.wait_until_done == bool)

    def test_synthetic_filter_wheel_methods(self):
        assert hasattr(self.synthetic_filter, 'filter_change_delay') and callable(getattr(self.synthetic_filter, 'filter_change_delay'))
        assert hasattr(self.synthetic_filter, 'set_filter') and callable(getattr(self.synthetic_filter, 'set_filter'))
        assert hasattr(self.synthetic_filter, 'read') and callable(getattr(self.synthetic_filter, 'read'))
        assert hasattr(self.synthetic_filter, 'close') and callable(getattr(self.synthetic_filter, 'close'))

    def test_synthetic_filter_wheel_method_calls(self):
        self.synthetic_filter.filter_change_delay(filter_name='Empty-Alignment')
        self.synthetic_filter.set_filter(filter_name='Empty-Alignment')
        self.synthetic_filter.read(num_bytes=1)
        self.synthetic_filter.close()
        pass

if (__name__ == "__main__"):
    unittest.main()

