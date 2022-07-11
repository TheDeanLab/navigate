"""
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

# Standard Library Imports
import unittest

# Third Party Imports
import numpy as np
import pytest

# Local Imports
# sys.path.append('../../../')


"""
Delete the below assert once the calculate entropy function is found
"""
def test_entropy():
    assert True


try:
    # from aslm.model.aslm_analysis import Analysis as aslm_analysis
    from aslm.model.aslm_debug_model import calculate_entropy

    class TestASLMAnalysis(unittest.TestCase):
        """
        Unit Tests for the ASLM Analysis Module
        """
        @pytest.mark.skip(reason='file path not found')
        def test_calculate_entropy_on(self):
            """
            Test the calculation of the Shannon Entropy
            """
            dct_array = np.ones((128, 128))
            otf_support_x = 3
            otf_support_y = 3
            # This trys to call from the aslm_analysis module however its only located in the aslm_debug_model
            # entropy = aslm_analysis.calculate_entropy()
            entropy = calculate_entropy(self,
                                                      dct_array=dct_array,
                                                      otf_support_x=otf_support_x,
                                                      otf_support_y=otf_support_y)
            self.assertEqual(entropy, 0)
except ImportError as e:
    print(e)

if (__name__ == "__main__"):
    unittest.main()
