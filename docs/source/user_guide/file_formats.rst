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
benchmarks on a RedHat Linux system. We assessed the median disk write time for TIFF,
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
   | 512x512     | 0.83    | 10.0     | 1.69  | 3.02  | 1.09    |
   +-------------+---------+----------+-------+-------+---------+
   | 1024x1024   | 1.55    | 10.4     | 6.46  | 5.70  | 2.27    |
   +-------------+---------+----------+-------+-------+---------+
   | 2048x2048   | 11.2    | 38.6     | 28.8  | 19.6  | 11.6    |
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
   | 512x512      | 0.14    | 0.13     | 2.64  | 1.58  | 1.05    |
   +--------------+---------+----------+-------+-------+---------+
   | 1024x1024    | 0.49    | 0.48     | 10.6  | 5.08  | 4.06    |
   +--------------+---------+----------+-------+-------+---------+
   | 2048x2048    | 1.92    | 1.86     | 52.7  | 13.90 | 8.50    |
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
