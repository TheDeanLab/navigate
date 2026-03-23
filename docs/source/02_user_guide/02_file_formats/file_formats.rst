.. _file_formats:

======================
Supported File Formats
======================

The choice of file format for saving imaging data in microscopy is crucial because it
affects write speed, data integrity, accessibility, and analysis efficiency. In
**navigate**, OME-Zarr is now the primary save format because it combines standardized
microscopy metadata with chunked, multiscale storage for large multidimensional
datasets. It also matches the storage contract used by the lab's downstream analysis
software, reducing format translation steps and keeping acquisition and analysis
tightly coupled.

To support both modern analysis workflows and compatibility with existing tools,
**navigate** writes OME-Zarr and OME-TIFF. OME, or Open Microscopy Environment, is a
standardized metadata model that helps ensure imaging data can be accurately
understood, shared, and analyzed across different software platforms and research
groups.

.. note::

    The performance of saving to these data sources is limited by write speed to disk. To achieve maximal saving speed, we recommend saving all data to a local solid state drive. See :ref:`Hardware Considerations <computer_considerations>` for more information.

File Types
----------

OME-Zarr
~~~~~~~~

**navigate** uses `zarr <https://zarr.readthedocs.io/en/stable/>`_ and
`ome-zarr-models <https://ome-zarr-models-py.readthedocs.io/en/stable/>`_ to write
acquisitions in the `OME-NGFF 0.5 <https://ngff.openmicroscopy.org/0.5/index.html>`_
format. Each acquisition is materialized as ``data_store.ome.zarr`` inside the save
directory. The store root is written as a single-well HCS plate with synthetic well
``A/1``, and each Navigate position is saved as one field image beneath that well.
Field images are stored as multiscale ``TCZYX`` arrays named ``0``, ``1``, ``2``, and
so on.

OME-Zarr is the recommended default for new acquisitions because it scales well to
large multidimensional and multi-position datasets, keeps rich acquisition metadata
close to the image data, and leaves room for future derived data such as labels or
tables in the same datastore. During acquisition, **navigate** writes the
full-resolution level first and finalizes the multiscale pyramid when the acquisition
closes.

OME-TIFF
~~~~~~~~

**navigate** uses the `tifffile <https://pypi.org/project/tifffile/>`_ package to
write OME-TIFF data to file. The **navigate** package creates a custom
:doc:`OME-TIFF XML <../../05_reference/_autosummary/navigate.model.metadata_sources.ome_tiff_metadata.OMETIFFMetadata>`
to store metadata. OME-TIFF remains available as a compatibility format for workflows
that expect TIFF-based interchange or software that does not yet read the current
OME-Zarr layout.

-------------------

Historical Image Writing Benchmarks
-----------------------------------

The benchmark tables below were collected on the previous file-writing stack and are
retained as historical context. They are useful for showing the general disk-speed
limits involved in microscopy acquisition, but they should not be interpreted as a
benchmark of the current OME-Zarr v0.5 / Zarr v3 writer.

To evaluate the historical save-path performance, we conducted benchmarks on a
Windows 10 system. We assessed the median disk write time for TIFF, OME-TIFF, H5, N5,
and OME-Zarr formats across image resolutions of 512x512, 1024x1024, and 2048x2048
under two conditions: (A) capturing 1000 single-plane images and (B) acquiring a
single z-stack composed of 1000 planes. All times are measured in milliseconds.
Results are presented below. For z-stack imaging, TIFF and OME-TIFF formats achieved
write speeds of up to approximately 300 Hz for a 2048x2048 camera resolution,
surpassing the operational speeds of most contemporary sCMOS cameras. The Big-TIFF
variant was used for both TIFF and OME-TIFF formats to accommodate the large file
sizes.

Timelapse Imaging
~~~~~~~~~~~~~~~~~

1000 images acquired, with a single Z plane. Median write time reported in milliseconds.

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

1 image acquired, with 1000 Z planes. Median write time reported in milliseconds.

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

In the historical H5/N5 measurements, initial setup introduced significant overhead,
and to a lesser extent TIFF and OME-TIFF did as well, which elevated the average
write time. However, the median write time remained consistently low and stable
across most of the acquisition.

Computer Specifications for Benchmarks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The computer specifications that the benchmarks were performed on are as follows.

- CPU: Intel(R) Xeon(R) Silver 4112 CPU @ 2.60GHz
- Memory: 88 GB
- Hard Drive: Micron 5200 ECO 7680 GB SSD
