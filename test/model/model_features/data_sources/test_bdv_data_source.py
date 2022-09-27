import os

import numpy as np


def test_bdv_write():
    from aslm.model.dummy import DummyModel
    from aslm.model.model_features.data_sources.bdv_data_source import BigDataViewerDataSource

    # Set up model with a random number of z-steps to modulate the shape
    model = DummyModel()
    z_steps = np.random.randint(1,10)
    model.experiment.MicroscopeState['number_z_steps'] = z_steps

    # Establish a BDV data source
    ds = BigDataViewerDataSource('test.h5')
    ds.set_metadata_from_configuration_experiment(model.configuration, model.experiment)

    # Populate one image per channel per timepoint
    n_images = ds.shape_c*ds.shape_z*ds.shape_t
    # TODO: Why does 2**16 make ImageJ crash??? But 2**8 works???
    data = (np.random.rand(n_images, ds.shape_x, ds.shape_y)*2**8).astype('uint16')
    data_positions = (np.random.rand(n_images, 5)*50e3).astype(float)
    for i in range(n_images):
        ds.write(data[i,...].squeeze(), x=data_positions[i,0], y=data_positions[i,1],
                 z=data_positions[i,2], theta=data_positions[i,3], f=data_positions[i,4])
    ds.close()

    try:
        os.remove(ds.file_name)
        xml_fn = '.'.join(ds.file_name.split('.')[:-1])+'.xml'
        os.remove(xml_fn)
    except PermissionError:
        # Windows seems to think these files are still open
        pass
    
    assert(True)
