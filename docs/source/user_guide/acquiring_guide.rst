==============
Acquiring Data
==============

This provides detailed descriptions of **navigate's** acquisition modes and 
saving capabilites. For a how to on acquiring data, please see 
:doc:`Acquiring an Image <beginner>`.

Standard Acquisition Modes
==========================

**navigate** features standard acquisition modes including Continous/Live, Single Frame
and Z-Stack, which can be saved to TIFF, H5 and N5 data formats. Saving is toggled under 
the GUI's :ref:`timepoint settings <user_guide/gui_walkthrough:timepoint settings>`.

These modes (and other custom modes) can be selected in the program's 
:ref:`acquisition bar <user_guide/gui_walkthrough:acquisition bar>` dropdown list.

Each acquisition mode is implemented as a :doc:`feature list <features>` and can be used 
in sequence with other features that can, for example, 
:doc:`make smart decisions <../intermediate>`.

Continuous Scan
---------------

This creates a live view of what is on the camera. It is not possible to save data in
this mode, only to preview what is in focus. This mode is helpful for alignment, 
parameter tuning, and scrolling around the sample with the stage. 

It is implemented as
a :ref:`feature list <user_guide/features:custom feature lists>`, shown in its 
:ref:`textual form <user_guide/features:text representation of feature lists>` below.

.. code-block:: python

    [
      (
        {"name": PrepareNextChannel},
        {
            "name": LoopByCount,
            "args": ("experiment.MicroscopeState.selected_channels",),
        },
      )
    ]

The sequence begins with the `PrepareNextChannel` features and loops over 
`experiment.MicroscopeState.selected_channels`. As such, continuous mode will
display a live preview of all 
:ref:`selected color channels <user_guide/gui_walkthrough:channel settings>` in 
sequence, then return the first color channel and start again.

Single Acquisition
------------------

This takes a single image of each 
:ref:`selected channel <user_guide/gui_walkthrough:channel settings>` and optionally 
saves them to a file. Its feature list is identical to that of "Continuous Scan".

Z-Stack Acquisition
-------------------

This takes an image stack over the range and at the step size defined by the
:ref:`stack acquisition settings <user_guide/gui_walkthrough:stack acquisition settings>`
and optionally saves the stack to a file. The color channels will appear as in 
continuous scan and single acquisition if :guilabel:`Laser Cycling Settings` is set to
"Per Z" in the stack acquisition settings. A single z-stack will be taken for each 
color channel, one channel at a time, if :guilabel:`Laser Cycling Settings` is set to 
"Per Stack".

Z-Stack acquisition is implemented as the feature list below.

.. code-block:: python

    [
        (
            {"name": ZStackAcquisition},
            {"name": StackPause},
            {
                "name": LoopByCount,
                "args": ("experiment.MicroscopeState.timepoints",),
            },
        )
    ]

Note that in the z-stack the color channel looping is abstracted into 
``ZStackAcquisition``, but we will take one set of z-stacks at each 
:ref:`timepoint <user_guide/gui_walkthrough:timepoint settings>`. It is also
worth noting that ``ZStackAcquisition`` handles moving through 
:ref:`multiple positions <user_guide/gui_walkthrough:multiposition>`.
``ZStackAcquisition`` will loop over z or c first, as decided by "Per Stack" 
or "Per Z", and then will loop over positions.

Projection
----------

`Projection mode <https://www.nature.com/articles/s41592-021-01175-7>`_ scans a light
sheet through a sample and sums the full 3D stack as a single image. It is useful for
fast overviews of 3D data. 

It is implemented as the feature list

.. code-block:: python

    [{"name": PrepareNextChannel}]

The magic of projection mode comes from changing the galvo operation to sweep the light
sheet through the whole sample during the course of a single frame.

Customized
----------

Customized acquisition mode can be used to run any feature list of the user's choosing.
Data acquisition with 
``navigate`` is almost infinitely reconfigurable with the either the 
:doc:`feature container <features>`, if a desired acquisition can be 
performed using a reconfiguration of existing features and saving formats, or the 
:doc:`plugin architecture <../plugin/plugin_home>`, if new features or saving formats are
required. We strongly recommend the reader check through the 
:doc:`available features <../_autosummary/navigate.model.features>` and see if they can be
combined into a acquisition feature list before writing a new acquisition feature.

Saving Formats
==============

``navigate`` comes pre-packaged with TIFF, OME-TIFF, and H5/N5 
(`BigDataViewer <https://imagej.net/plugins/bdv/>`_) file saving formats. The 
performance of these saving data sources is limited by write speed to disk. To 
achieve maximal saving speed, we recommend saving all data to a local SSD. See 
:ref:`Hardware Considerations <software_installation:hardware considerations>` for more
information.

TIFF/OME-TIFF
-------------

``navigate`` uses the `tifffile <https://pypi.org/project/tifffile/>`_ package to write
TIFF, BigTIFF, and OME-TIFF data to file. The ``navigate`` package creates a custom 
:doc:`OME-TIFF XML <../_autosummary/navigate.model.metadata_sources.ome_tiff_metadata.OMETIFFMetadata>`
to store metadata.

BigDataViewer H5/N5
-------------------

``navigate`` uses `h5py <https://docs.h5py.org/en/stable/index.html>`_ (H5) and
`zarr <https://zarr.readthedocs.io/en/stable/>`_ (N5) to store data in a BigDataViewer
file format. This is a pyramidal format, necessating the saving of both the original
data and downsampled versions of this data. The additional data slows down the write
speed. The N5 format is faster than H5 because it allows multithreaded writes.

Image Pipeline
==============

Images are stored from the camera onto a circular buffer of size ``databuffer_size``, a
setting under ``experiment.CameraParameters`` in the 
:doc:`software configuration <software_configuration>`. By default, this
buffer is 100 frames in length. 

Image processing and saving operations (see the
:doc:`feature container <../contributing/feature_container>` data operations) are 
performed on frames in this buffer. These operations must take less time than it takes 
to add a new frame to the buffer, or the buffer will eventually overflow. This is, in 
part, why saving to SSD (as opposed to HDD) is critical.
