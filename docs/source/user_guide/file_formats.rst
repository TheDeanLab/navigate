======================
Supported File Formats
======================

The choice of file format for saving imaging data in microscopy is crucial
because it affects data integrity, accessibility, and analysis efficiency.
Formats like TIFF and its derivative OME-TIFF are widely used due to their ability
to store metadata and support multiple imaging channels. However, modern formats such
as Zarr, N5, and HDF5, including OME-ZARR, cater to the needs of large-scale,
multi-dimensional datasets by enabling efficient data storage, access, and processing at
cloud-compute scales.

To enable ambitious imaging projects, **navigate** **navigate** comes pre-packaged with TIFF, OME-TIFF, OME-Zarr, HDF5/N5
(`BigDataViewer <https://imagej.net/plugins/bdv/>`_) file saving formats.
OME, or Open Microscopy Environment, is a standardized metadata model that ensures
that imaging data can be accurately understood, shared, and analyzed across different software
platforms and research groups.

.. Note::

    The performance of saving to these data sources is limited by write speed to disk. To
    achieve maximal saving speed, we recommend saving all data to a local solid state drive. See
    :ref:`Hardware Considerations <software_installation:hardware considerations>` for more
    information.

----------------

TIFF/OME-TIFF
-------------

**navigate** uses the `tifffile <https://pypi.org/project/tifffile/>`_ package to write
TIFF, BigTIFF, and OME-TIFF data to file. The **navigate** package creates a custom
:doc:`OME-TIFF XML <../_autosummary/navigate.model.metadata_sources.ome_tiff_metadata.OMETIFFMetadata>`
to store metadata.

----------------

BigDataViewer H5/N5/OME-Zarr
-------------------

**navigate** uses `h5py <https://docs.h5py.org/en/stable/index.html>`_ (H5) and
`zarr <https://zarr.readthedocs.io/en/stable/>`_ (N5) to store data in a BigDataViewer
file format. This is a pyramidal format, necessitating the saving of both the original
data and down sampled versions of this data. The additional data slows down the write
speed. The N5 format is faster than H5 because it allows multithreaded writes.
