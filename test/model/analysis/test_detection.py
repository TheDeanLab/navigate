# import unittest
from PIL import Image
import matplotlib.pyplot as plt
import sys

# sys.path.append('../../../src/model/analysis')
# from detection import add_median_border

# class TestDetection(unittest.TestCase):
class TestDetection:
    def test_add_median_border(self):
        # test_data = Image.open('https://samples.fiji.sc/blobs.png')
        data = np.zeros(50)
        # plt.plot(smooth_waveform(tunable_lens_ramp(), 10))
        plt.plot(data)
        plt.show()

if (__name__ == "__main__"):

    TestDetection.test_add_median_border()