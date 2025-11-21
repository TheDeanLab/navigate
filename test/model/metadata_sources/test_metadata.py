import pytest
import random


def test_metadata_voxel_size(dummy_model):
    from navigate.model.metadata_sources.metadata import Metadata

    md = Metadata()

    md.configuration = dummy_model.configuration

    zoom = dummy_model.configuration["experiment"]["MicroscopeState"]["zoom"]
    active_microscope = dummy_model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    pixel_size = float(
        dummy_model.configuration["configuration"]["microscopes"][active_microscope][
            "zoom"
        ]["pixel_size"][zoom]
    )

    dx, dy, dz = md.voxel_size

    assert (
        (dx == pixel_size)
        and (dy == pixel_size)
        and (
            dz
            == float(
                dummy_model.configuration["experiment"]["MicroscopeState"]["step_size"]
            )
        )
    )


def test_metadata_shape(dummy_model):
    from navigate.model.metadata_sources.metadata import Metadata

    dummy_model.configuration["experiment"]["MicroscopeState"]["image_mode"] = "z-stack"

    md = Metadata()

    md.configuration = dummy_model.configuration

    microscope_name = dummy_model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    txs = dummy_model.configuration["experiment"]["CameraParameters"][microscope_name][
        "img_x_pixels"
    ]
    tys = dummy_model.configuration["experiment"]["CameraParameters"][microscope_name][
        "img_y_pixels"
    ]
    tzs = dummy_model.configuration["experiment"]["MicroscopeState"]["number_z_steps"]
    tts = dummy_model.configuration["experiment"]["MicroscopeState"]["timepoints"]
    tcs = sum(
        [
            v["is_selected"] is True
            for k, v in dummy_model.configuration["experiment"]["MicroscopeState"][
                "channels"
            ].items()
        ]
    )

    xs, ys, cs, zs, ts = md.shape

    assert (xs == txs) and (ys == tys) and (zs == tzs) and (ts == tts) and (cs == tcs)


@pytest.mark.parametrize(
    "image_mode",
    [
        "single",
        "Confocal Projection",
        "z-stack",
    ],
)
@pytest.mark.parametrize("stack_cycling_mode", ["per_stack", "per_z"])
@pytest.mark.parametrize("conpro_cycling_mode", ["per_stack", "per_plane"])
def test_metadata_set_stack_order_from_configuration_experiment(
    dummy_model, image_mode, stack_cycling_mode, conpro_cycling_mode
):
    from navigate.model.metadata_sources.metadata import Metadata

    dummy_model.configuration["experiment"]["MicroscopeState"][
        "image_mode"
    ] = image_mode
    dummy_model.configuration["experiment"]["MicroscopeState"][
        "stack_cycling_mode"
    ] = stack_cycling_mode
    dummy_model.configuration["experiment"]["MicroscopeState"][
        "conpro_cycling_mode"
    ] = conpro_cycling_mode

    md = Metadata()

    md.configuration = dummy_model.configuration

    if image_mode == "z-stack" and stack_cycling_mode == "per_stack":
        assert md._per_stack is True
    elif image_mode == "Confocal Projection" and stack_cycling_mode == "per_stack":
        assert md._per_stack is True
    else:
        assert md._per_stack is False

def set_shape_from_configuration_experiment(dummy_model):
    from navigate.model.metadata_sources.metadata import Metadata

    md = Metadata()

    md.configuration = dummy_model.configuration.copy()


    # set up experiment with multiposition
    # no position
    md.configuration["experiment"]["MicroscopeState"]["image_mode"] = "z-stack"
    md.configuration["multi_positions"] = [
        ["X", "Y", "Z", "THETA", "F"]
    ]
    md.configuration["expriment"]["MicroscopeState"]["is_multiposition"] = False

    md._set_shape_from_configuration_experiment()

    assert md._multiposition is False
    assert md.positions == 1

    # customized mode
    md.configuration["experiment"]["MicroscopeState"]["image_mode"] = "customized"
    assert md._multiposition is True
    assert md.positions == 1

    # random multiposition
    md.configuration["experiment"]["MicroscopeState"]["image_mode"] = "z-stack"
    for i in range(5):
        num_positions = random.randint(2, 10)
        md.configuration["multi_positions"] = [["X", "Y", "Z", "THETA", "F"]]
        for p in range(num_positions):
            pos = [
                random.uniform(0, 100),  # X
                random.uniform(0, 100),  # Y
                random.uniform(0, 100),  # Z
                random.uniform(0, 360),  # THETA
                random.uniform(0, 10),  # F
            ]
            md.configuration["multi_positions"].append(pos)

        md.configuration["experiment"]["MicroscopeState"]["is_multiposition"] = True

        md._set_shape_from_configuration_experiment()

        assert md._multiposition is True
        assert md.positions == num_positions


