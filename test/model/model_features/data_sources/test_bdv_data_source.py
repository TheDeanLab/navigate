import os

import numpy as np

def test_bdv_write_read():
    from aslm.model.dummy_model import get_dummy_model
    from aslm.model.model_features.data_sources.bdv_data_source import BigDataViewerDataSource

    # Set up model with a random number of z-steps to modulate the shape
    model = get_dummy_model()
    z_steps = np.random.randint(1,10)
    model.experiment.MicroscopeState['number_z_steps'] = z_steps

    # Establish a BDV data source
    ds = BigDataViewerDataSource('test.h5')
    ds.set_metadata_from_configuration_experiment(model.configuration, model.experiment)

    # Populate one image per channel per timepoint
    n_images = ds.shape_c*ds.shape_z*ds.shape_t
    data = np.random.rand(n_images, ds.shape_x, ds.shape_y)
    for i in range(n_images):
        ds.write(data[i,...].squeeze(), x=1, y=1, z=1, theta=1, f=1)
    ds.close()

    try:
        os.remove(ds.file_name)
        xml_fn = '.'.join(ds.file_name.split('.')[:-1])+'.xml'
        os.remove(xml_fn)
    except PermissionError:
        # Windows seems to think these files are still open
        pass