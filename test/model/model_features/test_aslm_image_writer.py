from aslm.model.model_features.aslm_image_writer import ImageWriter
from aslm.model.dummy_model import get_dummy_model
# /Users/daxcollison/Documents/GitHub/ASLM/test/model/dummy_model.py


class TestImageWriter:

    def test_zarr_byslice(self):
        
        # False for no GPU
        dummy_model = get_dummy_model() 
        slicetest = ImageWriter(dummy_model)

        assert True

    
    def test_zarr_bymultislice(self):
        

        assert True


    def test_zarr_bystack(self):
        
        assert True

    def test_zarr_bymultistack(self):
        

        assert True