"""Configuration capability checks for idle position polling."""

import pytest

from navigate.config.stage_settings import stage_position_polling_supported


@pytest.mark.parametrize(
    "kind",
    [
        "ASI",
        "MS2000",
        "MFC2000",
        "Synthetic",
        "ASIStage",
        "asi.MS2000",
        "synthetic.SyntheticStage",
    ],
)
def test_supported_stage_aliases(kind):
    assert stage_position_polling_supported({"hardware": {"type": kind}})


@pytest.mark.parametrize("kind", ["MP285", "PI", "NI", "MCL", "custom.ASI", ""])
def test_unsupported_stage_types(kind):
    assert not stage_position_polling_supported({"hardware": [{"type": kind}]})


def test_mixed_configuration_and_virtual_devices():
    assert stage_position_polling_supported(
        {"hardware": [{"type": "MP285"}, {"type": "Synthetic"}]}
    )
    assert stage_position_polling_supported(
        {"hardware": [{"type": "MP285"}]}, synthetic_hardware=True
    )
    assert not stage_position_polling_supported({"hardware": []})
