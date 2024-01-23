""" File type specific data sources. """

FILE_TYPES = ["TIFF", "OME-TIFF", "H5", "N5"]


def get_data_source(file_type):
    """Get the data source class for the given file type.

    Parameters
    ----------
    file_type : str
        File type to get the data source for.

    Returns
    -------
    DataSource
        Data source class for the given file type.

    Examples
    --------
    >>> get_data_source('tif')
    <class 'navigate.model.data_sources.tif.TifDataSource'>
    """

    if (file_type == "TIFF") or (file_type == "OME-TIFF"):
        from .tiff_data_source import TiffDataSource

        return TiffDataSource

    elif (file_type == "H5") or file_type == ("N5"):
        from .bdv_data_source import BigDataViewerDataSource

        return BigDataViewerDataSource

    else:
        raise NotImplementedError(f"Unknown file type {file_type}. Cannot open.")
