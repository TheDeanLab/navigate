import os


def test_bdv_metadata(dummy_model):
    from aslm.model.metadata_sources.bdv_metadata import BigDataViewerMetadata

    md = BigDataViewerMetadata()

    views = []
    for idx in range(10):
        views.append(
            {
                "x": dummy_model.data_buffer_positions[idx][0],
                "y": dummy_model.data_buffer_positions[idx][1],
                "z": dummy_model.data_buffer_positions[idx][2],
                "theta": dummy_model.data_buffer_positions[idx][3],
                "f": dummy_model.data_buffer_positions[idx][4],
            }
        )

    md.write_xml("test_bdv.xml", views)

    os.remove("test_bdv.xml")
