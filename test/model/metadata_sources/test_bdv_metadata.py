import os
import numpy as np

import pytest


@pytest.mark.parametrize("ext", ["h5", "n5", "tiff"])
def test_bdv_metadata(ext):
    from navigate.model.metadata_sources.bdv_metadata import BigDataViewerMetadata

    md = BigDataViewerMetadata()

    views = []
    for _ in range(10):
        views.append(
            {
                "x": np.random.randint(-1000, 1000),
                "y": np.random.randint(-1000, 1000),
                "z": np.random.randint(-1000, 1000),
                "theta": np.random.randint(-1000, 1000),
                "f": np.random.randint(-1000, 1000),
            }
        )

    for view in views:
        arr = md.stage_positions_to_affine_matrix(**view)
        assert arr[0, 3] == view["y"] / md.dy
        assert arr[1, 3] == view["x"] / md.dx
        assert arr[2, 3] == view["z"] / md.dz

    md.write_xml(f"test_bdv.{ext}", views)

    os.remove("test_bdv.xml")

    # Test defaults for shear transform.
    assert md.rotate_data is False
    assert md.shear_data is False
    assert np.shape(md.rotate_transform) == (3, 4)
    assert np.shape(md.shear_transform) == (3, 4)

    # Confirm that the shear/rotation transforms are identity matrices by default
    assert np.all(md.shear_transform == np.eye(3, 4))
    assert np.all(md.rotate_transform == np.eye(3, 4))

    # Confirm that the shear/rotation transforms are identity matrices by default
    # even after calling calculate_shear_transform and calculate_rotate_transform
    md.bdv_shear_transform()
    md.bdv_rotate_transform()
    assert np.all(md.shear_transform == np.eye(3, 4))
    assert np.all(md.rotate_transform == np.eye(3, 4))

    # Test that the shear/rotation transforms are correctly calculated.
    md.shear_data = True
    md.shear_dimension = "XZ"
    md.shear_angle = 15
    md.dx, md.dy, md.dz = 1, 1, 1
    md.bdv_shear_transform()
    assert md.shear_transform[0, 2] == np.tan(np.deg2rad(15))

    md.rotate_data = True
    md.rotate_angle_x = 15
    md.rotate_angle_y = 0
    md.rotate_angle_z = 0
    md.bdv_rotate_transform()
    assert md.rotate_transform[1, 1] == np.cos(np.deg2rad(15))
    assert md.rotate_transform[1, 2] == -np.sin(np.deg2rad(15))
    assert md.rotate_transform[2, 1] == np.sin(np.deg2rad(15))
    assert md.rotate_transform[2, 2] == np.cos(np.deg2rad(15))

    # Make sure we can still write the data.
    md.write_xml(f"test_bdv.{ext}", views)
    os.remove("test_bdv.xml")

@pytest.mark.parametrize("stack_cycling_mode", ["per_stack", "per_z"])
def test_bdv_xml_dict(dummy_model, stack_cycling_mode):
    from navigate.model.metadata_sources.bdv_metadata import BigDataViewerMetadata

    md = BigDataViewerMetadata()

    md.configuration = dummy_model.configuration.copy()

    # set shape from configuration and experiment
    md.configuration["experiment"]["MicroscopeState"]["image_mode"] = "z-stack"

    # timepoints, channels, z-slices, positions
    for tp in [1]: #, 2, 3, 5]:
        for pos in [1, 3, 5]:
            for ch in [1, 2, 3]:
                for z in [1, 5, 10, 20]:
                    md.configuration["experiment"]["MicroscopeState"]["timepoints"] = tp
                    # channel settings
                    channel_dict = md.configuration["experiment"]["MicroscopeState"]["channels"]
                    for i in range(1, ch+1):
                        channel_name = f"channel_{i}"
                        if channel_name not in channel_dict:
                            channel_dict[channel_name] = {
                                "is_selected": True,
                                "laser": "488nm",
                                "laser_index": 0,
                                "camera_exposure_time": 200.0,
                                "laser_power": 20.0,
                                "interval_time": 1.0,
                                "defocus": 104.0,
                                "filter_wheel_0": "Empty-Alignment",
                                "filter_position_0": 6,
                                "filter_wheel_1": "Empty-Alignment",
                                "filter_position_1": 6
                            }
                        else:
                            channel_dict[channel_name]["is_selected"] = True
                    for i in range(ch+1, 5):
                        channel_name = f"channel_{i}"
                        if channel_name in channel_dict:
                            channel_dict[channel_name]["is_selected"] = False
                    # z-stack settings
                    start_z_position = md.configuration["experiment"]["MicroscopeState"]["start_position"]
                    md.configuration["experiment"]["MicroscopeState"]["number_z_steps"] = z
                    md.configuration["experiment"]["MicroscopeState"]["step_size"] = 0.2
                    md.configuration["experiment"]["MicroscopeState"]["end_position"] = z * 0.2 + start_z_position
                    # multiposition settings
                    md.configuration["experiment"]["MicroscopeState"]["is_multiposition"] = (
                        True if pos > 1 else False
                    )
                    multipositions = [
                        ["X", "Y", "Z", "THETA", "F"]
                    ]
                    for p in range(pos):
                        position = [
                            np.random.uniform(0, 100),  # X
                            np.random.uniform(0, 100),  # Y
                            np.random.uniform(0, 100),  # Z
                            np.random.uniform(0, 360),  # THETA
                            np.random.uniform(0, 10),  # F
                        ]
                        multipositions.append(position)

                    md.configuration["multi_positions"] = multipositions

                    md.set_from_configuration_experiment()

                    assert md.shape_t == tp
                    assert md.shape_c == ch
                    assert md.shape_z == z
                    assert md.positions == pos

                    if pos > 1:
                        assert md._multiposition is True
                    else:
                        assert md._multiposition is False

                    # view
                    views = []
                    for p in range(1, pos):
                        for c in range(ch):
                            position = md.configuration["multi_positions"][p + 1]
                            for _z in range(z):
                                views.append(
                                    {
                                        "x": position[0],
                                        "y": position[1],
                                        "z": position[2] + start_z_position + _z * 0.2,
                                        "theta": position[3],
                                        "f": position[4],
                                    }
                                )

                    xml_dict = md.bdv_xml_dict("test_file.h5", views)

                    assert "ImageLoader" in xml_dict["SequenceDescription"]
                    assert "ViewSetups" in xml_dict["SequenceDescription"]
                    assert "Timepoints" in xml_dict["SequenceDescription"]
                    assert "ViewRegistrations" in xml_dict
                    # verify affine values are the same for a position
                    view_registrations = xml_dict["ViewRegistrations"]["ViewRegistration"]
                    for i in range(len(view_registrations)):
                        # assert view id
                        view_id = view_registrations[i]["setup"]
                        if ch > 1:
                            assert view_id == ((i % ch) * pos + (i // ch))
                        # assert affine position consistency between channels
                        if i % ch == 0:
                            affine = view_registrations[i]["ViewTransform"][0]["affine"]["text"]
                        else:
                            affine_c = view_registrations[i]["ViewTransform"][0]["affine"]["text"]
                            assert affine == affine_c


def test_bdv_xml_dict_angle_tile_mapping():
    from navigate.model.metadata_sources.bdv_metadata import BigDataViewerMetadata

    md = BigDataViewerMetadata()
    md.dx = md.dy = md.dz = 1
    md.shape_x = 10
    md.shape_y = 12
    md.shape_z = 1
    md.shape_c = 1
    md.shape_t = 1
    md.positions = 3

    views = [
        {"x": 0.0, "y": 0.0, "z": 0.0, "theta": 0.0, "f": 0.0},
        {"x": 0.0, "y": 0.0, "z": 0.0, "theta": 60.0, "f": 0.0},
        {"x": 0.0, "y": 0.0, "z": 0.0, "theta": 120.0, "f": 0.0},
    ]

    xml_dict = md.bdv_xml_dict("test_file.n5", views)

    view_setups = xml_dict["SequenceDescription"]["ViewSetups"]["ViewSetup"]
    assert len(view_setups) == 3

    angle_attrs = xml_dict["SequenceDescription"]["ViewSetups"]["Attributes"][3][
        "Angle"
    ]
    tile_attrs = xml_dict["SequenceDescription"]["ViewSetups"]["Attributes"][2]["Tile"]

    assert len(tile_attrs) == 1
    assert [a["id"]["text"] for a in angle_attrs] == ["0", "1", "2"]

    assert [vs["attributes"]["tile"]["text"] for vs in view_setups] == ["0", "0", "0"]
    assert [vs["attributes"]["angle"]["text"] for vs in view_setups] == [
        "0",
        "1",
        "2",
    ]
