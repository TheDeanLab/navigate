==========================
Imaging on an Upright ASLM
==========================

This case study outlines how to use **navigate** for imaging on an upright ASLM microscope.
Here, the specimen is positioned with an Applied Scientific Instrumentation FTP-2000 stage, which
permits imaging samples with large lateral extents. Moreover, the stage can be moved at a constant
velocity during imaging, which allows for acquisition of data without delays introduced by stage communication protocols and
settling times.

To achieve this, **navigate** receives a `trigger signal <http://www.asiimaging.com/docs/scan_module>`_
from the stage controller to start image acquisition once
the stage has reached the desired position and velocity. Thereafter, **navigate** acquires images
at a constant rate until the stage has reached the end position. This mode of acquisition is termed
"Constant Velocity Acquisition", and is implemented as a plugin in **navigate**. To
download the plugin, please visit `navigate-constant-velocity-acquisition
<https://github.com/TheDeanLab/navigate-constant-velocity-acquisition>`_.

Since the stage moves at a 45 degree angle relative to the microscope detection axis,
computational shearing of the data is necessary. For large data sets, this can become computationally challenging and
unnecessarily results in greater data overhead owing to empty space introduced in the data.
To avoid this, we also provide a guide on how to perform two axis stage
scanning which removes the need for computational shearing.
More information about this microscope and this method, which we refer to as mechanical shearing, can be found
`here <https://www.biorxiv.org/content/10.1101/2024.04.10.588892v1>`_.

.. Constant Velocity Acquisition:

Imaging a Z-Stack using Constant Velocity Acquisition Mode
==========================================================

#. Select `Continuous Scan` from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Using the :guilabel:`Stage Control`, go to a shallow Z-position in the sample. Under
   the :guilabel:`Channels` tab, in :guilabel:`Stack Acquisition Settings (um)` press
   :guilabel:`Set Start Pos`.
#. Go to a deep Z-position in the sample. Press :guilabel:`Set End Pos`.
#. Make sure :guilabel:`Set Foc` is ``0`` for both the :guilabel:`Set Start Pos` and
   :guilabel:`End Pos`.
#. Type the desired step size (units um) in the :guilabel:`Step Size` dialog box in
   :guilabel:`Stack Acquisition Settings (um)`. Note: The step size represents the
   optical step size. The velocity at which the stage moves during imaging accounts for the shear angle.
#. Select the number of color channels needed imaging in the :guilabel:`Channel tab`
   under :guilabel:`Channel Settings`. Select the correct filter for each channel by
   using the dropdown menu after each channel under the :guilabel:`Filter`.
#. Change the exposure time by changing number in the :guilabel:`Exp. Time (ms)` for
   each channel. For the ORCA Lightning camera using ASLM mode, the maximum exposure time is 100 ms.
#. Set :guilabel:`Interval` to be ``1.0`` for each channel.
#. Set :guilabel:`Defocus` to be ``0`` for each channel.
#. Select "Constant Velocity Acquisition" from the dropdown next to the
   :guilabel:`Acquire` button. Press :guilabel:`Acquire`.
#. Enter the sample parameters in the :guilabel:`File Saving Dialog` that pops up. Make
   sure to save to SSD drive or change buffer size in configuration file to prevent any
   overwriting of images. Then Press :guilabel:`Acquire Data`. The stage will move from its current position to beyond the start position.
   The stage then ramps up to the desired stage velocity as the stage reaches the start position.
   Once the stage is at the start position, the stage will send an external trigger which
   is received by the DAQ to begin image acquisition. The number of frames required for
   each channel scan is precalculated from the stage velocity, scan distance, and single
   frame acquisition time. Acquisition will automatically stop when the desired number of
   frames are acquired which also corresponds to when the stage reaches its end position.
   For multichannel scans, the stage returns to the start position and the process repeats until all channels are acquired.
#. To change frame buffer size, in the :guilabel:`CameraParameters` section in the
   :guilabel:`experiment.yaml` file in your local navigate directory in the
   :guilabel:`config` folder, change :guilabel:`databuffer_size` to desired number of
   frames. Make sure the size of the desired number of frames isn't above the available
   RAM in the computer.

   .. z_stack:

Imaging a Z-Stack using two-axis scanning
============================================

#. Select `Continuous Scan` from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Using the :guilabel:`Stage Control` tab, go to a shallow z-position in the sample.
   Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquisition Settings (um)`
   press :guilabel:`Set Start Pos`.
#. Using the :guilabel:`Stage Control` tab, Go to a deep z-position in the sample.
#. Using the :guilabel:`Stage Control` tab, move the :guilabel:`Focus` button to match
   the z-axis scan distance. Make sure that the focus moves in the same direction as the z-scan.

.. note::

    One should pay attention to both the magnitude and the direction of the scan in both ``Z`` and ``F``.
    Scanning in ``F`` is accompanied with risk of crashing the stage into the objective. Importantly, the
    direction of travel varies depending upon the manufacturer.

#. Move Press :guilabel:`Set End Pos`.
#. Make sure :guilabel:`Set Foc` is the same range as :guilabel:`Set Start Pos` and
   :guilabel:`End Pos`.
#. Type the desired step size (units um) in the :guilabel:`Step Size` dialog box in
   :guilabel:`Stack Acquisition Settings (um)`.
#. Select the number of color channels needed imaging in the :guilabel:`Channel tab`
   under :guilabel:`Channel Settings`. Select the correct filter for each channel by
   using the dropdown menu after each channel under the :guilabel:`Filter`.
#. Change the exposure time by changing number in the :guilabel:`Exp. Time (ms)` for
   each channel. For the ORCA Lightning camera using ASLM mode, the minimum frame rate
   is 75 ms and the maximum is 100 ms.
#. Set :guilabel:`Interval` to be ``1.0`` for each channel.
#. Set :guilabel:`Defocus` to be ``0`` for each channel.
#. Select "Z-Stack" from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`.
#. Enter the sample parameters in the :guilabel:`File Saving Dialog` that pops up.
   Press :guilabel:`Acquire Data`. This will move the stage in the z-axis and the x-axis
   before imaging a plane during the z-stack. Move the stage at the same angle as the
   shearing angle removes the need for computational shearing which can be computationally cumbersome.
