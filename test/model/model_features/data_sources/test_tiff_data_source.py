import os

import numpy as np

def tiff_write_read(is_ome=False, multiposition=False):
    from aslm.model.dummy_model import get_dummy_model
    from aslm.model.model_features.data_sources.tiff_data_source import TiffDataSource

    # Set up model with a random number of z-steps to modulate the shape
    model = get_dummy_model()
    z_steps = np.random.randint(1,10)
    model.experiment.MicroscopeState['image_mode'] = 'z-stack'
    model.experiment.MicroscopeState['number_z_steps'] = z_steps
    if multiposition:
        model.experiment.MicroscopeState['is_multiposition'] = True

    # Establish a TIFF data source
    if is_ome:
        fn = 'test.ome.tif'
    else:
        fn = ''
    ds = TiffDataSource(fn)
    ds.set_metadata_from_configuration_experiment(model.configuration, model.experiment)

    # Populate one image per channel per timepoint per positioj
    n_images = ds.shape_c*ds.shape_z*ds.shape_t*ds.positions
    data = np.random.rand(n_images, ds.shape_x, ds.shape_y)
    file_names = []
    for i in range(n_images):
        ds.write(data[i,...].squeeze())
        c, z, _, _ = ds._cztp_indices(i, True)
        if c == 0 and z == 0:
            file_names.extend(ds.file_name)
    ds.close()

    # For each file...
    for i, fn in enumerate(file_names):
        ds2 = TiffDataSource(fn, 'r')
        # Make sure XYZ size is correct (and C and T are each of size 1)
        assert((ds2.shape_x == ds.shape_x) and (ds2.shape_y == ds.shape_y) \
                and (ds2.shape_c == 1) and (ds2.shape_z == ds.shape_z) \
                and (ds2.shape_t == 1))
        # Make sure the data copied properly
        np.testing.assert_equal(ds2.data, data[i*ds.shape_z:(i+1)*ds.shape_z,...].squeeze())
        ds2.close()

    try:
        # Clean up
        dirs = []
        for fn in file_names:
            os.remove(fn)
            dirs.append(os.path.dirname(fn))
        for dn in list(set(dirs)):
            print(dn)
            os.rmdir(dn)
    except PermissionError:
        # Windows seems to think these files are still open
        pass


def test_tiff_write_read():
    tiff_write_read(False)

def test_tiff_write_read_ome():
    tiff_write_read(True)

def test_tiff_write_read_ome_multiposition():
    tiff_write_read(True, True)
