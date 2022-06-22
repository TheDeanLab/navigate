from aslm.model.model_features.aslm_image_writer import ImageWriter
from aslm.model.dummy_model import get_dummy_model
import numpy as np


class TestImageWriter:
        

    def test_zarr_byslice(self):

        self.dummy_model = get_dummy_model()
        # Creating 3D simulated data in this case a 3D F shape
        self.data_buffer = None
        
        slicetest = ImageWriter(self.dummy_model)




        assert True

    
    def test_zarr_bymultislice(self):
        

        assert True


    def test_zarr_bystack(self):
        
        assert True

    def test_zarr_bymultistack(self):
        

        assert True