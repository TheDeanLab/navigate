import sys
import types
import pytest
from navigate.model.data_sources import get_data_source


# Dummy classes for data source tests
class DummyTiffDataSource:
    pass


class DummyBigDataViewerDataSource:
    pass


class DummyOMEZarrDataSource:
    pass


def setup_dummy_modules(monkeypatch):
    # Create dummy modules for testing purposes
    tiff_module = types.ModuleType("navigate.model.data_sources.tiff_data_source")
    tiff_module.TiffDataSource = DummyTiffDataSource
    monkeypatch.setitem(
        sys.modules, "navigate.model.data_sources.tiff_data_source", tiff_module
    )

    bdv_module = types.ModuleType("navigate.model.data_sources.bdv_data_source")
    bdv_module.BigDataViewerDataSource = DummyBigDataViewerDataSource
    monkeypatch.setitem(
        sys.modules, "navigate.model.data_sources.bdv_data_source", bdv_module
    )

    zarr_module = types.ModuleType("navigate.model.data_sources.zarr_data_source")
    zarr_module.OMEZarrDataSource = DummyOMEZarrDataSource
    monkeypatch.setitem(
        sys.modules, "navigate.model.data_sources.zarr_data_source", zarr_module
    )


@pytest.fixture
def dummy_modules(monkeypatch):
    setup_dummy_modules(monkeypatch)


def test_get_data_source_tiff(dummy_modules):
    result = get_data_source("TIFF")
    assert result is DummyTiffDataSource


def test_get_data_source_ometiff(dummy_modules):
    result = get_data_source("OME-TIFF")
    assert result is DummyTiffDataSource


def test_get_data_source_h5(dummy_modules):
    result = get_data_source("H5")
    assert result is DummyBigDataViewerDataSource


def test_get_data_source_n5(dummy_modules):
    result = get_data_source("N5")
    assert result is DummyBigDataViewerDataSource


def test_get_data_source_ome_zarr(dummy_modules):
    result = get_data_source("OME-Zarr")
    assert result is DummyOMEZarrDataSource


def test_get_data_source_invalid(dummy_modules, caplog):
    with pytest.raises(NotImplementedError) as excinfo:
        get_data_source("INVALID_TYPE")
    assert "Unknown file type" in str(excinfo.value)
    # Check that an error message was logged
    assert any("Unknown file type" in record.message for record in caplog.records)
