==========================
Imaging on an Upright ASLM
==========================

This is a case study in using the software to image with an upright ASLM microscope. The upright ASLM equipped with an ASI FTP2000 and an ASLM microscope in an upright configuration. This microscope configuration allows for imaging across large scan ranges and imaging during scanning which we term constant velocity acquisition. This tutorial aims to show how it is possible to image the sample while imaging in both ASLM mode and normal lightsheet mode.


Loading and finding the sample
==============================

#. Load the sample on the microscope.
#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Scroll around with the stage either via joystick or using the controls in the
   :guilabel:`Stage Control` tab until the sample comes into view.
#. Set the resonant galvo :guilabel:`Galvo 0` to 0.3 to mitigate any striping artifacts
   during imaging.

.. z_stack:

Imaging a Z-Stack using Stop and Settle Mode
============================================

#. Select :guilabel:`Continuous Scan` from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Using the :guilabel:`Stage Control`, go to a shallow z-position in the sample.
   Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)`
   press :guilabel:`Set Start Pos`.
#. Go to a deep z-position in the sample. Press :guilabel:`Set End Pos`.
#. Make sure :guilabel:`Set Foc` is ``0`` for both the :guilabel:`Set Start Pos` and
   :guilabel:`End Pos`.
#. Type the desired step size (units um) in the :guilabel:`Step Size` dialog box in
   :guilabel:`Stack Acquistion Settings (um)`. Step size can only be in increments of
   0.1 and the minimum is 0.2.
#. Select the number of color channels needed imaging in the :guilabel:`Channel tab`
   under :guilabel: `Channel Settings`. Select the correct filter for each channel by
   using the dropdown menu after each channel under the :guilabel:`Filter`.
#. Change the exposure time by changing number in the :guilabel:`Exp. Time (ms)` for
   each channel. For the ORCA Lightning camera using ASLM mode, the minimum frame rate
   is 75 ms and the maximum is 100 ms.
#. Set :guilabel:`Interval` to be ``1.0`` for each channel.
#. Set :guilabel:`Defocus` to be ``0`` for each channel.
#. Select "Z-Stack" from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`.
#. Enter the sample parameters in the :guilabel:`File Saving Dialog` that pops up.
   Press :guilabel:`Acquire Data`.

.. Constant Velocity Acquisition:

Imaging a Z-Stack using Constant Velocity Acquisition Mode
==========================================================

#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Using the :guilabel:`Stage Control`, go to a shallow Z-position in the sample. Under
   the :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)` press
   :guilabel:`Set Start Pos`.
#. Go to a deep Z-position in the sample. Press :guilabel:`Set End Pos`.
#. Make sure :guilabel:`Set Foc` is ``0`` for both the :guilabel:`Set Start Pos` and
   :guilabel:`End Pos`.
#. Type the desired step size (units um) in the :guilabel:`Step Size` dialog box in
   :guilabel:`Stack Acquistion Settings (um)`. Step size can only be increments of
   0.1 and the minimum is 0.2.
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
   overwriting of images. Then Press :guilabel:`Acquire Data`.
#. To change frame buffer size, in the :guilabel:`CameraParameters` section in the
   :guilabel:`experiment.yaml` file in your local navigate directory in the
   :guilabel:`config` folder, change :guilabel:`databuffer_size` to desired number of
   frames. Make sure the size of the desired number of frames isn't above the available
   RAM in the computer.
