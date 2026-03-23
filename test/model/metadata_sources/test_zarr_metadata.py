import pytest


@pytest.fixture
def dummy_metadata(dummy_model):
    from navigate.model.metadata_sources.zarr_metadata import OMEZarrMetadata

    metadata = OMEZarrMetadata()
    metadata.configuration = dummy_model.configuration
    return metadata


def test_axes(dummy_metadata):
    axes = dummy_metadata.axes

    assert [axis.name for axis in axes] == ["t", "c", "z", "y", "x"]
    assert axes[0].type == "time"
    assert axes[0].unit == "second"
    assert axes[1].type == "channel"
    assert [axis.type for axis in axes[2:]] == ["space", "space", "space"]
    assert all(axis.unit == "micrometer" for axis in axes[2:])


def test_stage_positions_to_translation_transform(dummy_metadata):
    translation = dummy_metadata._stage_positions_to_translation_transform(
        10.0, 20.0, 30.0, 40.0, 50.0
    )

    assert len(translation) == len(dummy_metadata.axes)
    assert translation[:2] == [0.0, 0.0]
    assert translation[2:] == [30.0, 20.0, 10.0]


def test_scale_transform(dummy_metadata):
    assert dummy_metadata._scale_transform(1) == [
        1.0,
        1.0,
        dummy_metadata.dz,
        dummy_metadata.dy,
        dummy_metadata.dx,
    ]
    assert dummy_metadata._scale_transform(4) == [
        1.0,
        1.0,
        dummy_metadata.dz * 4,
        dummy_metadata.dy * 4,
        dummy_metadata.dx * 4,
    ]


def test_coordinate_transformations(dummy_metadata):
    scale = dummy_metadata._scale_transform(2)
    translation = dummy_metadata._stage_positions_to_translation_transform(
        1.0, 2.0, 3.0, 4.0, 5.0
    )

    transforms = dummy_metadata._coordinate_transformations(scale)
    assert len(transforms) == 1
    assert transforms[0].type == "scale"

    transforms = dummy_metadata._coordinate_transformations(scale, translation)
    assert len(transforms) == 2
    assert transforms[0].type == "scale"
    assert transforms[1].type == "translation"


def test_ngff_attribute_builders(dummy_metadata):
    hcs_attrs = dummy_metadata.hcs_attributes(positions=3)
    assert hcs_attrs["ome"]["version"] == "0.5"
    assert hcs_attrs["ome"]["plate"]["field_count"] == 3
    assert hcs_attrs["ome"]["plate"]["wells"][0]["path"] == "A/1"

    well_attrs = dummy_metadata.well_attributes(["0", "1", "2"])
    assert well_attrs["ome"]["well"]["images"] == [
        {"path": "0"},
        {"path": "1"},
        {"path": "2"},
    ]

    image_attrs = dummy_metadata.image_attributes(
        name="Field 0",
        paths=["0", "1", "2"],
        scale_factors=[1, 2, 4],
        view={"x": 1.0, "y": 2.0, "z": 3.0, "theta": 4.0, "f": 5.0},
    )
    multiscale = image_attrs["ome"]["multiscales"][0]
    assert multiscale["name"] == "Field 0"
    assert [dataset["path"] for dataset in multiscale["datasets"]] == ["0", "1", "2"]
    assert multiscale["axes"][0]["name"] == "t"

    labels_attrs = dummy_metadata.labels_attributes(["cells", "nuclei"])
    assert labels_attrs["ome"]["labels"] == ["cells", "nuclei"]

    xml = dummy_metadata.metadata_only_xml(["0", "1"])
    assert "Field 0" not in xml
    assert "Image:0" in xml
