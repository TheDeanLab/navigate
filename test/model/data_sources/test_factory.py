import sys
import types
from unittest.mock import Mock

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


def test_get_data_source_logs_and_raises_for_unknown_type(monkeypatch):
    logger = Mock()
    monkeypatch.setattr(data_sources, "logger", logger)

    with pytest.raises(NotImplementedError, match="Unknown file type CSV. Cannot open."):
        data_sources.get_data_source("CSV")

    logger.error.assert_called_once_with("Unknown file type CSV. Cannot open.")
