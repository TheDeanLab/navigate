import runpy

import pytest

import navigate.model.devices.objectives as objectives_module
from navigate.model.devices.objectives import Objective


EXPECTED_TABLE = {
    "N40X_NIR": 8.0,
    "N16XLWD-PF": 20.0,
    "N25X-APO-MP": 17.6,
    "54-10-12": 9.6,
    "54-12-8": 11.76,
}


def test_calculate_entrance_pupil_regression_for_entire_default_table():
    obj = Objective()

    # Lock the default objective table so unexpected additions/removals fail loudly.
    assert set(obj.properties.keys()) == set(EXPECTED_TABLE.keys())

    for objective_name, expected_entrance_pupil in EXPECTED_TABLE.items():
        result = obj.calculate_entrance_pupil(objective_name)
        assert result == pytest.approx(expected_entrance_pupil)


def test_calculate_entrance_pupil_uses_olympus_tube_lens():
    obj = Objective()
    obj.properties["OLY-TEST"] = {
        "manufacturer": "Olympus",
        "numerical_aperture": 0.5,
        "focal_length": 9,
    }

    result = obj.calculate_entrance_pupil("OLY-TEST")
    assert result == pytest.approx(9.0)


def test_calculate_entrance_pupil_raises_for_unknown_objective():
    obj = Objective()
    with pytest.raises(KeyError):
        obj.calculate_entrance_pupil("does-not-exist")


@pytest.mark.parametrize(
    "missing_key",
    ("focal_length", "numerical_aperture", "manufacturer"),
)
def test_calculate_entrance_pupil_raises_key_error_for_missing_required_field(
    missing_key,
):
    obj = Objective()
    broken_definition = {
        "manufacturer": "ASI",
        "numerical_aperture": 0.4,
        "focal_length": 12,
    }
    del broken_definition[missing_key]
    obj.properties["BROKEN"] = broken_definition

    with pytest.raises(KeyError, match=missing_key):
        obj.calculate_entrance_pupil("BROKEN")


def test_calculate_entrance_pupil_raises_for_zero_focal_length():
    obj = Objective()
    obj.properties["ZERO-FOCAL"] = {
        "manufacturer": "ASI",
        "numerical_aperture": 0.4,
        "focal_length": 0,
    }

    with pytest.raises(ZeroDivisionError):
        obj.calculate_entrance_pupil("ZERO-FOCAL")


def test_objectives_module_main_prints_expected_message(capsys):
    runpy.run_path(objectives_module.__file__, run_name="__main__")
    output = capsys.readouterr().out

    assert "The entrance pupil diameter for the" in output
    assert "54-10-12" in output
    assert "9.6" in output
    assert "mm." in output
