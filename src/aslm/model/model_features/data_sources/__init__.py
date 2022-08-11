def get_data_source(file_type):
    if (file_type == 'TIFF') or (file_type == 'OME-TIFF'):
        from .tiff_data_source import TiffDataSource
        return TiffDataSource
    elif file_type == 'Zarr':
        from .zarr_data_source import ZarrDataSource
        return ZarrDataSource
    elif file_type == 'BDV':
        from .bdv_data_source import BigDataViewerDataSource
        return BigDataViewerDataSource
    else:
        raise NotImplementedError(f"Unknown file type {file_type}. Cannot open.")
