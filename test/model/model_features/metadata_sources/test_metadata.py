from aslm.model.dummy_model import get_dummy_model

def test_metadata_voxel_size():
    from aslm.model.model_features.metadata_sources.metadata import Metadata

    model = get_dummy_model()

    md = Metadata()

    md.configuration = model.configuration
    md.experiment = model.experiment

    zoom = model.experiment.MicroscopeState['zoom']
    if model.experiment.MicroscopeState['resolution_mode'] == 'low':
        pixel_size = float(model.configuration.ZoomParameters['low_res_zoom_pixel_size'][zoom])
    else:
        pixel_size = float(model.configuration.ZoomParameters['high_res_zoom_pixel_size'])

    dx, dy, dz = md.voxel_size

    print(dx, dy, dz)

    assert((dx == pixel_size) and (dy == pixel_size) and (dz == float(model.experiment.MicroscopeState['step_size'])))

def test_metadata_shape():
    from aslm.model.model_features.metadata_sources.metadata import Metadata

    model = get_dummy_model()

    md = Metadata()

    md.configuration = model.configuration
    md.experiment = model.experiment

    txs = model.experiment.CameraParameters['x_pixels']
    tys = model.experiment.CameraParameters['y_pixels']
    tzs = model.experiment.MicroscopeState['number_z_steps']
    tts = model.experiment.MicroscopeState['timepoints']
    tcs = sum([v['is_selected'] == True for k, v in model.experiment.MicroscopeState['channels'].items()])

    xs, ys, zs, ts, cs = md.shape

    assert((xs==txs) and (ys==tys) and (zs==tzs) and (ts==tts) and (cs==tcs))
