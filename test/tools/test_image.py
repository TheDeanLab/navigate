# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
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

# Standard Library Imports
import unittest

# Third-Party Imports
import numpy as np
from PIL import Image

# Local Imports
from aslm.tools.image import text_array, create_arrow_image


class TextArrayTestCase(unittest.TestCase):
    def test_text_array(self):
        text = "55"
        offset = (0, 0)

        result = text_array(text, offset)

        # Assert that the result is a numpy array
        self.assertIsInstance(result, np.ndarray)

        # Assert that the values in the result array are either True or False
        assert result.dtype is np.dtype("bool")

    def test_text_array_output_type(self):
        """Confirm output is np.ndarray object"""
        text_output = text_array(text="ASLM")
        assert type(text_output) == np.ndarray

    def test_text_array_output_height(self):
        """Confirm that the output is approximately the correct height

        Initially thought that the height should be ~= font_size, but this
        turned out to be much more variable than I anticipated
        """
        text = "ASLM"
        text_output = text_array(text=text)
        height = np.shape(text_output)[0]
        width = np.shape(text_output)[1]
        expected_width = ((len(text) * height) / 2) + 2
        expected_height = 11
        assert width == expected_width
        assert height == expected_height


class TestCreateArrowImage(unittest.TestCase):

    def test_create_arrow_image(self):
        xys = [(50, 50), (150, 50), (200, 100)]
        image = create_arrow_image(xys, direction="right")
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.width, 300)
        self.assertEqual(image.height, 200)

        xys = [(50, 50), (150, 50), (200, 100)]
        image = create_arrow_image(xys, 400, 300, direction="left")
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.width, 400)
        self.assertEqual(image.height, 300)

        image2 = create_arrow_image(xys, 500, 400, direction="up", image=image)
        self.assertIsInstance(image2, Image.Image)
        self.assertEqual(image2.width, 400)
        self.assertEqual(image2.height, 300)
        assert image == image2

        image3 = create_arrow_image(xys, 500, 400, direction="down", image=image)
        self.assertIsInstance(image3, Image.Image)
        self.assertEqual(image3.width, 400)
        self.assertEqual(image3.height, 300)
        assert image == image3



if __name__ == "__main__":
    unittest.main()
