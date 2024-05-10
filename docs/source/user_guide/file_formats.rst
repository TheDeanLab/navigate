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
----------------------------

**navigate** uses `h5py <https://docs.h5py.org/en/stable/index.html>`_ (H5) and
`zarr <https://zarr.readthedocs.io/en/stable/>`_ (N5) to store data in a BigDataViewer
file format. This is a pyramidal format, necessitating the saving of both the original
data and down sampled versions of this data. The additional data slows down the write
speed. The N5 format is faster than H5 because it allows multithreaded writes.

----------------

Image Writing Benchmarks
------------------------

To evaluate the performance of saving imaging data in different formats, we conducted
benchmarks on a Linux-based system. We assessed the median disk write time for TIFF,
OME-TIFF, H5, N5, and OME-Zarr formats across image resolutions of 512x512,
1024x1024, and 2048x2048 under two conditions: (A) capturing 1000 single-plane
images and (B) acquiring a single z-stack composed of 1000 planes. All times
are measured in milliseconds. Results are presented below. For z-stack imaging, TIFF
and OME-TIFF formats achieved write speeds of up to approximately 400 Hz for a 2048x2048 camera
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
   | 512x512     | 4.06    | 15.26    | 2.79  | 12.09 | 1.35    |
   +-------------+---------+----------+-------+-------+---------+
   | 1024x1024   | 6.69    | 15.25    | 8.33  | 14.74 | 2.46    |
   +-------------+---------+----------+-------+-------+---------+
   | 2048x2048   | 22.25   | 38.57    | 34.71 | 29.56 | 11.85   |
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
   | 512x512      | 0.21    | 0.17     | 4.76  | 1.80  | 1.30    |
   +--------------+---------+----------+-------+-------+---------+
   | 1024x1024    | 0.52    | 0.57     | 15.70 | 5.38  | 4.22    |
   +--------------+---------+----------+-------+-------+---------+
   | 2048x2048    | 2.35    | 2.14     | 75.56 | 14.08 | 8.60    |
   +--------------+---------+----------+-------+-------+---------+

Additional Sources of Overhead
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The initial setup for writing H5/N5 files introduces
significant overhead, and to a lesser extent for TIFF and OME-TIFF files, which
elevates the average write time. However, the median write time remains consistently
low and stable across most of the acquisition.

Computer Specifications for Benchmarks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The computer specifications that the benchmarks were performed on are as follows:

-   Architecture: x86_64
-   CPU operational modes: 32-bit, 64-bit
-   Number of CPUs: 72
-   Threads per core: 2
-   Cores per socket: 18
-   CPU Model: Intel(R) Xeon(R) Gold 6354 CPU @ 3.00GHz
-   CPU Speed: 883.850 MHz
-   Memory: 0.5 TB
