import os

import numpy as np

def test_write_shape():
    from aslm.model.dummy_model import get_dummy_model
    from aslm.model.model_features.data_sources.tiff_data_source import TiffDataSource

    # Set up model with a random number of z-steps to modulate the shape
    model = get_dummy_model()
    z_steps = np.random.randint(0,10)
    model.experiment.MicroscopeState['number_z_steps'] = z_steps

    # Establish a TIFF data source
    ds = TiffDataSource()
    ds.set_metadata_from_configuration_experiment(model.configuration, model.experiment)

    # Populate one image per channel per timepoint
    for _ in range(ds.shape_c*ds.shape_z*ds.shape_t):
        data = np.random.rand(ds.shape_x, ds.shape_y)
        ds.write(data)
    ds.close()

    # grab the file names (one file per channel per timepoint)
    files = ds.file_name

    # For each file, make sure XYZ size is correct (and C and T are each of size 1)
    for fn in files:
        ds2 = TiffDataSource(fn, 'r')
        assert((ds2.shape_x == ds.shape_x) and (ds2.shape_y == ds.shape_y) \
                and (ds2.shape_c == 1) and (ds2.shape_z == ds.shape_z) \
                and (ds2.shape_t == 1))

    # Clean up
    for fn in files:
        os.remove(fn)
