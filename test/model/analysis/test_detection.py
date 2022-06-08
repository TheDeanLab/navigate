# Standard Library Imports
import unittest
import sys

# Third Party Imports
import numpy as np

# Local Imports
sys.path.append('../../../../')
from src.model.analysis.detection import add_median_border

class TestDetection(unittest.TestCase):

    def test_matrix_expansion(self):
        data = np.random.rand(50, 50, 50)
        test_output = add_median_border(data)
        self.assertEqual(np.shape(test_output), (52, 52, 52))

    def test_median_border(self):
        data = np.random.rand(50, 50, 50)
        test_output = add_median_border(data)
        self.assertEqual(test_output[0, 0, 0], np.median(data))

if (__name__ == "__main__"):
    unittest.main()
