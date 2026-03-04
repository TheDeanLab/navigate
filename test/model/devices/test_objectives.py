import pytest

from navigate.model.devices.objectives import Objective


def test_calculate_entrance_pupil_for_known_objective():
    obj = Objective()
    result = obj.calculate_entrance_pupil("54-10-12")
    assert result == pytest.approx(9.6)


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
