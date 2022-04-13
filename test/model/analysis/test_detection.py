# Standard Library Imports
import unittest
import sys

# Third Party Imports
import numpy as np

# Local Imports
sys.path.append('../../../')
from src.model.analysis.detection import add_median_border

class TestDetection(unittest.TestCase):
    def test_add_median_border(self):
        data = np.zeros((50, 50, 50))
        test_output = add_median_border(data)
        print("Data Shape:", np.shape(test_output))
        self.assertEqual(np.shape(test_output), (52, 52, 52))

if (__name__ == "__main__"):
    unittest.main()
