import logging
import sys
import types

import pytest

from navigate.model import data_sources


@pytest.mark.parametrize(
    ("file_type", "module_name", "class_name"),
    [
        ("TIFF", "tiff_data_source", "TiffDataSource"),
        ("OME-TIFF", "tiff_data_source", "TiffDataSource"),
        ("H5", "bdv_data_source", "BigDataViewerDataSource"),
        ("N5", "bdv_data_source", "BigDataViewerDataSource"),
        ("OME-Zarr", "zarr_data_source", "OMEZarrDataSource"),
    ],
)
def test_get_data_source_returns_expected_class(
    monkeypatch, file_type, module_name, class_name
):
    fake_module_name = f"{data_sources.__name__}.{module_name}"
    fake_module = types.ModuleType(fake_module_name)
    fake_class = type(class_name, (), {})

    setattr(fake_module, class_name, fake_class)
    monkeypatch.setitem(sys.modules, fake_module_name, fake_module)

    assert data_sources.get_data_source(file_type) is fake_class


def test_get_data_source_logs_and_raises_for_unknown_type(caplog):
    with caplog.at_level(logging.ERROR, logger="model"):
        with pytest.raises(
            NotImplementedError, match="Unknown file type CSV. Cannot open."
        ):
            data_sources.get_data_source("CSV")

    assert "Unknown file type CSV. Cannot open." in caplog.text
