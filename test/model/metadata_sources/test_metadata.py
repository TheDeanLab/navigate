def test_metadata_voxel_size():
    from aslm.model.dummy import DummyModel
    from aslm.model.metadata_sources.metadata import Metadata

    model = DummyModel()

    md = Metadata()

    md.configuration = model.configuration

    zoom = model.configuration['experiment']['MicroscopeState']['zoom']
    active_microscope = model.configuration['experiment']['MicroscopeState']['microscope_name']
    pixel_size = float(model.configuration['configuration']['microscopes'][active_microscope]['zoom']['pixel_size'][zoom])

    dx, dy, dz = md.voxel_size

    assert((dx == pixel_size) and (dy == pixel_size) and (dz == float(model.configuration['experiment']['MicroscopeState']['step_size'])))


def test_metadata_shape():
    from aslm.model.dummy import DummyModel
    from aslm.model.metadata_sources.metadata import Metadata

    model = DummyModel()
    model.configuration['experiment']['MicroscopeState']['image_mode'] = 'z-stack'

    md = Metadata()

    md.configuration = model.configuration

    txs = model.configuration['experiment']['CameraParameters']['x_pixels']
    tys = model.configuration['experiment']['CameraParameters']['y_pixels']
    tzs = model.configuration['experiment']['MicroscopeState']['number_z_steps']
    tts = model.configuration['experiment']['MicroscopeState']['timepoints']
    tcs = sum([v['is_selected'] == True for k, v in model.configuration['experiment']['MicroscopeState']['channels'].items()])

    xs, ys, cs, zs, ts = md.shape

    assert((xs==txs) and (ys==tys) and (zs==tzs) and (ts==tts) and (cs==tcs))
