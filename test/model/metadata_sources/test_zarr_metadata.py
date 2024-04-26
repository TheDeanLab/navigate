import pytest

SPACE_UNITS = [
    "angstrom",
    "attometer",
    "centimeter",
    "decimeter",
    "exameter",
    "femtometer",
    "foot",
    "gigameter",
    "hectometer",
    "inch",
    "kilometer",
    "megameter",
    "meter",
    "micrometer",
    "mile",
    "millimeter",
    "nanometer",
    "parsec",
    "petameter",
    "picometer",
    "terameter",
    "yard",
    "yoctometer",
    "yottameter",
    "zeptometer",
    "zettameter",
]

TIME_UNITS = [
    "attosecond",
    "centisecond",
    "day",
    "decisecond",
    "exasecond",
    "femtosecond",
    "gigasecond",
    "hectosecond",
    "hour",
    "kilosecond",
    "megasecond",
    "microsecond",
    "millisecond",
    "minute",
    "nanosecond",
    "petasecond",
    "picosecond",
    "second",
    "terasecond",
    "yoctosecond",
    "yottasecond",
    "zeptosecond",
    "zettasecond",
]


@pytest.fixture
def dummy_metadata(dummy_model):
    from navigate.model.metadata_sources.zarr_metadata import OMEZarrMetadata

    # Create metadata
    md = OMEZarrMetadata()

    md.configuration = dummy_model.configuration

    return md


def test_axes(dummy_metadata):

    axes = dummy_metadata._axes

    # Check length
    assert (len(axes) > 1) and (len(axes) < 6)

    # Check list types and count
    time_count = 0
    space_count = 0
    channel_count = 0
    custom_count = 0
    for d in axes:
        if d["type"] == "time":
            assert d["unit"] in TIME_UNITS
            time_count += 1
        elif d["type"] == "space":
            assert d["unit"] in SPACE_UNITS
            space_count += 1
        elif d["type"] == "channel":
            channel_count += 1
        else:
            custom_count += 1

    assert (space_count > 1) and (space_count < 4)
    assert time_count < 2
    assert ((channel_count < 2) and (custom_count == 0)) or (
        (channel_count == 0) and (custom_count < 2)
    )

    # Check order
    order_type = [x["type"] for x in axes]
    if "time" in order_type:
        # Time must be first, if present
        assert order_type.index("time") == 0
    if "channel" in order_type:
        # Channel must be before all the space axes, if present
        ci = order_type.index("channel")
        for i, el in enumerate(order_type):
            if el == "space":
                assert i > ci

    # Skip zyx order spec as the naming of axes is not enforcable.


def test_stage_positions_to_translation_transform(dummy_metadata):
    import random

    pos = [random.random() for _ in range(5)]

    translation = dummy_metadata._stage_positions_to_translation_transform(*pos)

    axes = dummy_metadata._axes

    assert len(translation) == len(axes)


def test_scale_transform(dummy_metadata):
    scale = dummy_metadata._scale_transform()

    axes = dummy_metadata._axes

    assert len(scale) == len(axes)


def test_coordinate_transformations(dummy_metadata):
    import random

    pos = [random.random() for _ in range(5)]

    translation = dummy_metadata._stage_positions_to_translation_transform(*pos)
    scale = dummy_metadata._scale_transform()

    assert len(dummy_metadata._coordinate_transformations(scale)) == 1

    combo = dummy_metadata._coordinate_transformations(scale, translation)
    assert len(combo) == 2
    assert combo[0]["type"] == "scale" and combo[1]["type"] == "translation"

    with pytest.raises(UserWarning):
        dummy_metadata._coordinate_transformations(translation=translation)


def test_multiscale_metadata(dummy_metadata):
    """https://ngff.openmicroscopy.org/0.4/#multiscale-md"""
    import numpy as np
    import random

    resolutions = np.array([[1, 1, 1], [2, 2, 1], [4, 4, 1], [8, 8, 1]], dtype=int)
    paths = [f"path{i}" for i in range(resolutions.shape[0])]
    view = {k: random.random() for k in ["x", "y", "z", "theta", "f"]}

    msd = dummy_metadata.multiscales_dict("test", paths, resolutions, view)

    # Each "multiscales" dictionary MUST contain the field "axes"
    assert "axes" in msd.keys()

    # Each "multiscales" dictionary MUST contain the field "datasets"
    assert "datasets" in msd.keys()
    # Each dictionary in "datasets" MUST contain the field "path",
    # whose value contains the path to the array for this resolution
    # relative to the current zarr group. The "path"s MUST be ordered
    # from largest (i.e. highest resolution) to smallest.
    # Each "datasets" dictionary MUST have the same number of dimensions
    # and MUST NOT have more than 5 dimensions.

    # Each "multiscales" dictionary SHOULD contain the field "name"
    assert "name" in msd.keys()

    # Each "multiscales" dictionary MAY contain the field "coordinateTransformations"
    assert "coordinateTransformations" in msd.keys()

    # It SHOULD contain the field "version"
    assert "version" in msd.keys()

    # Each "multiscales" dictionary SHOULD contain the field "type", which gives
    # the type of downscaling method used to generate the multiscale image pyramid.
    # It SHOULD contain the field "metadata", which contains a dictionary with
    # additional information about the downscaling method.
