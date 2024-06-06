======================
Supported File Formats
======================

The choice of file format for saving imaging data in microscopy is crucial
because it affects write speed, data integrity, accessibility, and analysis efficiency.
Formats like TIFF and its derivative OME-TIFF are widely used due to their ability
to store metadata and support multiple imaging channels. However, modern formats such
as Zarr, N5, and HDF5, including OME-Zarr, cater to the needs of large-scale,
multi-dimensional datasets by enabling efficient data storage, access, and processing at
cloud-compute scales.

To enable ambitious imaging projects, **navigate** comes pre-packaged with TIFF, OME-TIFF, OME-Zarr,
and HDF5/N5 (`BigDataViewer <https://imagej.net/plugins/bdv/>`_) file saving formats.
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

BigDataViewer H5/N5
----------------------------

**navigate** uses `h5py <https://docs.h5py.org/en/stable/index.html>`_ (H5) and
`zarr <https://zarr.readthedocs.io/en/stable/>`_ (N5) to store data in a BigDataViewer
file format. This is a pyramidal format, necessitating the saving of both the original
data and down sampled versions of this data. The additional data slows down the write
speed. The N5 format can be faster than H5 because it allows for multithreaded writes.

OME-Zarr
--------
OME-Zarr is a Zarr file format that adheres to strict metadata specifications, detailed
at https://ngff.openmicroscopy.org/0.4/index.html. It allows for pyramidal data writing,
storage of segmentation labels with the data set, and updating the pyramidal structure
on the fly.


----------------

Image Writing Benchmarks
------------------------

To evaluate the performance of saving imaging data in different formats, we conducted
benchmarks on a Windows 10 system. We assessed the median disk write time for TIFF,
OME-TIFF, H5, N5, and OME-Zarr formats across image resolutions of 512x512,
1024x1024, and 2048x2048 under two conditions: (A) capturing 1000 single-plane
images and (B) acquiring a single z-stack composed of 1000 planes. All times
are measured in milliseconds. Results are presented below. For z-stack imaging, TIFF
and OME-TIFF formats achieved write speeds of up to approximately 300 Hz for a 2048x2048 camera
resolution, surpassing the operational speeds of most contemporary sCMOS cameras.
The Big-TIFF variant was used for both TIFF and OME-TIFF formats to accommodate the
large file sizes.

Timelapse Imaging
~~~~~~~~~~~~~~~~~

1000 images acquired, with a single Z plane. Median write time reported in
milliseconds.

.. table::
   :widths: auto
   :align: center

   +-------------+---------+----------+-------+-------+---------+
   |             | TIFF    | OME-TIFF | H5    | N5    | OME-Zarr|
   +=============+=========+==========+=======+=======+=========+
   | 512x512     | 1.19    | 29.24    | 3.17  | 9.00  | 5.30    |
   +-------------+---------+----------+-------+-------+---------+
   | 1024x1024   | 1.84    | 36.69    | 18.59 | 14.55 | 8.81    |
   +-------------+---------+----------+-------+-------+---------+
   | 2048x2048   | 5.55    | 44.65    | 84.18 | 38.60 | 25.02   |
   +-------------+---------+----------+-------+-------+---------+

Z-Stack Imaging
~~~~~~~~~~~~~~~

1 image acquired, with 1000 Z planes. Median write speed time in milliseconds.

.. table::
   :widths: auto
   :align: center

   +--------------+---------+----------+-------+-------+---------+
   |              | TIFF    | OME-TIFF | H5    | N5    | OME-Zarr|
   +==============+=========+==========+=======+=======+=========+
   | 512x512      | 0.28    | 0.25     | 7.30  | 5.10  | 3.29    |
   +--------------+---------+----------+-------+-------+---------+
   | 1024x1024    | 0.89    | 0.88     | 29.15 | 12.44 | 8.26    |
   +--------------+---------+----------+-------+-------+---------+
   | 2048x2048    | 4.12    | 3.30     | 135.74| 37.09 | 24.83   |
   +--------------+---------+----------+-------+-------+---------+

Additional Sources of Overhead
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The initial setup for writing H5/N5 files introduces
significant overhead, and to a lesser extent for TIFF and OME-TIFF files, which
elevates the average write time. However, the median write time remains consistently
low and stable across most of the acquisition.

Computer Specifications for Benchmarks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The computer specifications that the benchmarks were performed on are as follows.

-   CPU: Intel(R) Xeon(R) Silver 4112 CPU @ 2.60GHz
-   Memory: 88 GB
-   Hard Drive: Micron 5200 ECO 7680gb SSD
