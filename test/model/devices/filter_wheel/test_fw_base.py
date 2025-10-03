from navigate.model.devices.filter_wheel.synthetic import SyntheticFilterWheel
from test.model.dummy import DummyModel


def test_filter_wheel_base_functions():

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    fw = SyntheticFilterWheel(
        microscope_name=microscope_name,
        device_connection=None,
        configuration=model.configuration,
        device_id=0,
    )

    filter_dict = model.configuration["configuration"]["microscopes"][microscope_name][
        "filter_wheel"
    ][0]["available_filters"]

    assert fw.check_if_filter_in_filter_dictionary(list(filter_dict.keys())[0])
    try:
        fw.check_if_filter_in_filter_dictionary("not a filter")
    except ValueError:
        assert True
        return
    assert False
