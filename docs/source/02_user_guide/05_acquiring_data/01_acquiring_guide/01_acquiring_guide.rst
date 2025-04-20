==============
Acquiring Data
==============

This provides detailed descriptions of **navigate**'s acquisition modes and saving capabilities. For a how-to on acquiring data, please see :ref:`Acquiring an Image <beginner>`.

----------------

Standard Acquisition Modes
==========================

**navigate** features standard acquisition modes including Continuous/Live, Single Frame, and Z-Stack, which can be saved to TIFF, OME-TIFF, HDF5, N5, and OME-Zarr data formats. Saving is toggled under the GUI's :ref:`timepoint settings <ui_timepoint_settings>`.

These modes (and other custom modes) can be selected in the program's :ref:`acquisition bar <ui_acquisition_bar>` dropdown list. Each acquisition mode is implemented as a :ref:`feature list <user_guide_features>` and can be used in sequence with other features that can, for example, :ref:`make smart decisions <intermediate>`.

----------------

.. _user_guide_continuous:

Continuous Scan
---------------

This creates a live view of what is on the camera. It is not possible to save data in this mode, only to preview what is in focus. This mode is helpful for alignment, parameter tuning, and scrolling around the sample with the stage.

It is implemented as a :ref:`feature list <user_guide_features>`, shown in its :ref:`textual form <text_representation_features>` below.

.. code-block:: python

    [
      (
        {"name": PrepareNextChannel},
        {
            "name": LoopByCount,
            "args": ("channels",),
        },
      )
    ]

The sequence begins with the `PrepareNextChannel` feature and loops over `experiment.MicroscopeState.selected_channels`. As such, continuous mode will display a live preview of all :ref:`selected color channels <ui_channel_settings>` in sequence, then return the first color channel and start again.

----------------

Single Acquisition
------------------

This takes a single image of each :ref:`selected channel <ui_channel_settings>` and optionally saves them to a file. Its feature list is identical to that of "Continuous Scan".

----------------

Z-Stack Acquisition
-------------------

This takes an image stack over the range and at the step size defined by the :ref:`stack acquisition settings <ui_stack_settings>` and optionally saves the stack to a file. The color channels will appear as in "Continuous Scan" and "Single Acquisition" if :guilabel:`Laser Cycling Settings` is set to "Per Z" in the stack acquisition settings. A single z-stack will be taken for each color channel, one channel at a time, if :guilabel:`Laser Cycling Settings` is set to "Per Stack".

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

Note that in the z-stack the color channel looping is abstracted into ``ZStackAcquisition``, but we will take one set of z-stacks at each :ref:`timepoint <ui_timepoint_settings>`. It is also worth noting that ``ZStackAcquisition`` handles moving through :ref:`multiple positions <ui_multiposition>`. ``ZStackAcquisition`` will loop over ``Z`` or ``C`` first, as decided by "Per Stack" or "Per Z", and then will loop over positions.

----------------

Customized
----------

The customized acquisition mode can be used to run any feature list of the user's choosing. Data acquisition with **navigate** is almost infinitely reconfigurable with either the :ref:`feature container <user_guide_features>`, if a desired acquisition can be performed using a reconfiguration of existing features and saving formats, or the :ref:`plugin architecture <plugin>`, if new features or saving formats are required. We strongly recommend the reader check through the :ref:`available features <currently_implemented_features>` and see if they can be combined into an acquisition feature list before writing a new acquisition feature.

----------------

Analysis Pipeline
=================

Images are stored from the camera onto a circular buffer of size ``databuffer_size``. By default, this buffer is 100 frames in length.

Image processing and saving operations (see the :ref:`feature container <features>` data operations) are performed on frames in this buffer. These operations must take less time than it takes to add a new frame to the buffer, or the buffer will eventually overflow. This is, in part, why saving to an SSD (as opposed to HDD) is critical.
