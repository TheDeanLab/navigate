==========================
Imaging on an Upright ASLM
==========================

This is a case study in using the software to image with an upright ASLM microscope.
The upright ASLM equipped with an ASI FTP2000 and an ASLM microscope in an upright configuration.
This microscope configuration allows for imaging across long scan ranges and imaging during single axis stage scanning which we term constant velocity acquisition.
Acquiring images as the stage moves at a constant velocity enables fast isotropic volumetric imaging of samples. We provide a tutorial of how to implement constant velocity acquisition using Navigate.
Furthermore, since imaging is done at a 45 degree angle, deskewing large volumes of data is computationally demanding. We also provide a guide how to implement two axis stage scanning to remove the need for computational deskewing termed mechanical shearing. More information about this microscope and mechanical shearing can be found `here <https://www.biorxiv.org/content/10.1101/2024.04.10.588892v1>`_

.. Constant Velocity Acquisition:

Imaging a Z-Stack using Constant Velocity Acquisition Mode
==========================================================

#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Using the :guilabel:`Stage Control`, go to a shallow Z-position in the sample. Under
   the :guilabel:`Channels` tab, in :guilabel:`Stack Acquisition Settings (um)` press
   :guilabel:`Set Start Pos`.
#. Go to a deep Z-position in the sample. Press :guilabel:`Set End Pos`.
#. Make sure :guilabel:`Set Foc` is ``0`` for both the :guilabel:`Set Start Pos` and
   :guilabel:`End Pos`.
#. Type the desired step size (units um) in the :guilabel:`Step Size` dialog box in
   :guilabel:`Stack Acquisition Settings (um)`. Note: The step size represents the optical step size. The velocity at which the stage moves during imaging accounts for the shear angle.
#. Select the number of color channels needed imaging in the :guilabel:`Channel tab`
   under :guilabel:`Channel Settings`. Select the correct filter for each channel by
   using the dropdown menu after each channel under the :guilabel:`Filter`.
#. Change the exposure time by changing number in the :guilabel:`Exp. Time (ms)` for
   each channel. For the ORCA Lightning camera using ASLM mode, the minimum frame rate
   is 75 ms and the maximum is 100 ms.
#. Set :guilabel:`Interval` to be ``1.0`` for each channel.
#. Set :guilabel:`Defocus` to be `0` for each channel.
#. Select "Constant Velocity Acquisition" from the dropdown next to the
   :guilabel:`Acquire` button. Press :guilabel:`Acquire`.
#. Enter the sample parameters in the :guilabel:`File Saving Dialog` that pops up. Make
   sure to save to SSD drive or change buffer size in configuration file to prevent any
   overwriting of images. Then Press :guilabel:`Acquire Data`. The stage will move from its current position to beyond the start position.
   The stage then ramps up to the desired stage velocity as the stage reaches the start position. Once the stage is at the start position, the stage will send an external trigger which is recieved by the daq to begin image acquisition. The number of frames required for each channel scan is precalculated from the stage velocity, scan distance, and single frame acquisition time. Acquisition will automatically stop when the desired number of frames are acquired which also corresponds to when the stage reaches its end position. For multichannel scans, the stage moves beyond the start position, and the process repeats until all channels are acquired.
#. To change frame buffer size, in the :guilabel:`CameraParameters` section in the
   :guilabel:`experiment.yaml` file in your local navigate directory in the
   :guilabel:`config` folder, change :guilabel:`databuffer_size` to desired number of
   frames. Make sure the size of the desired number of frames isn't above the available
   RAM in the computer.

   .. z_stack:

Imaging a Z-Stack using two-axis scanning
============================================

#. Select :guilabel:`Continuous Scan` from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Using the :guilabel:`Stage Control` tab, go to a shallow z-position in the sample.
   Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquisition Settings (um)`
   press :guilabel:`Set Start Pos`.
#. Using the :guilabel:`Stage Control` tab, Go to a deep z-position in the sample.
#. Using the :guilabel:`Stage Control` tab, move the :guilabel:`Focus` button to match the z-axis scan distance. Make sure that the focus moves in the same direction as the z-scan.
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
   Press :guilabel:`Acquire Data`. This will move the stage in the z-axis and the x-axis before imaging a plane during the z-stack. Move the stage at the same angle as the shearing angle removes the need for computational shearing which can be computationally cumbersome.
