import pytest


@pytest.mark.hardware
def test_filter_wheel_sutter_init():
    from aslm.model.devices.filter_wheel.filter_wheel_sutter import (
        SutterFilterWheel,
        build_filter_wheel_connection,
    )
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    if (
        model.configuration["configuration"]["hardware"]["filter_wheel"]["type"]
        != "SutterFilterWheel"
    ):
        raise TypeError(
            f"Wrong filter wheel hardware specified {model.configuration['configuration']['hardware']['filter_wheel']['type'] != 'SutterFilterWheel'}"
        )
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]

    serial_controller = build_filter_wheel_connection(
        model.configuration["configuration"]["hardware"]["filter_wheel"]["port"],
        model.configuration["configuration"]["hardware"]["filter_wheel"]["baudrate"],
    )

    fw = SutterFilterWheel(microscope_name, serial_controller, model.configuration)


@pytest.mark.hardware
def test_filter_wheel_sutter_functions():
    import random

    from aslm.model.devices.filter_wheel.filter_wheel_sutter import (
        SutterFilterWheel,
        build_filter_wheel_connection,
    )
    from aslm.model.dummy import DummyModel

    model = DummyModel()
    if (
        model.configuration["configuration"]["hardware"]["filter_wheel"]["type"]
        != "SutterFilterWheel"
    ):
        raise TypeError(
            f"Wrong filter wheel hardware specified {model.configuration['configuration']['hardware']['filter_wheel']['type'] != 'SutterFilterWheel'}"
        )
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]

    serial_controller = build_filter_wheel_connection(
        model.configuration["configuration"]["hardware"]["filter_wheel"]["port"],
        model.configuration["configuration"]["hardware"]["filter_wheel"]["baudrate"],
    )

    fw = SutterFilterWheel(microscope_name, serial_controller, model.configuration)
    filter_names = [
        x for x in list(fw.filter_dictionary.keys()) if not x.startswith("Blocked")
    ]
    n_filters = len(filter_names) - 1

    print(filter_names)
    print(n_filters)

    funcs = ["filter_change_delay", "set_filter", "close"]
    args = [
        [filter_names[random.randint(0, n_filters)]],
        [filter_names[random.randint(0, n_filters)]],
        None,
    ]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(fw, f)(*a)
        else:
            getattr(fw, f)()
