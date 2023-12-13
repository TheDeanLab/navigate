def test_filter_wheel_base_functions():
    from navigate.model.devices.filter_wheel.filter_wheel_base import FilterWheelBase
    from navigate.model.dummy import DummyModel

    model = DummyModel()
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    fw = FilterWheelBase(microscope_name, None, model.configuration)

    filter_dict = model.configuration["configuration"]["microscopes"][microscope_name][
        "filter_wheel"
    ]["available_filters"]

    assert fw.check_if_filter_in_filter_dictionary(list(filter_dict.keys())[0])
    try:
        fw.check_if_filter_in_filter_dictionary("not a filter")
    except ValueError:
        assert True
        return
    assert False
