Case Study: Imaging on the Expansion ASLM
======================================

This is a case study in using the software to image with a `Expansion ASLM Microscope`.

Setting the beam parameters
---------------------------

Make sure the imaging chamber is empty or, if a sample is mounted, the sample is not in the beam path.
#. Mount chamber onto microscope stage and add dye solution for desired imaging wavelength into chamber.
#. Change cylindrical lens to spherical lens in setup.
#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Go to the :guilabel:`Channels` tab. Choose the wavelength you want to align. Set the laser's :guilabel:`Power` to `10.0` or lower. Change :guilabel:`Filter` to the appropiate filter for the imaging wavelength.
#. Go to the :menuselection:`Microscope Configuration --> Waveform Parameters`. A popup named :guilabel:`Waveform Parameter Settings` will appear. Make sure the :guilabel:`Mode` matches "Nanoscale" and the :guilabel:`Magnification` says N/A.
#. Set the desired imaging wavelength's :guilabel:`Amplitude` to `0.0`. Set the wavelength's :guilabel:`Offset` so that the beam is focused in the center of the field of view.
#. Go to :guilabel:`Camera Settings` and ensure that "Light-Sheet" is selected under :guilabel:`Sensor Mode`. Slowly increase the wavelength's :guilabel:`Amplitude` until the beam becomes a straight line across the screen. If the beam does not become straighter, try changing the camera's :guilabel:`Readout Direction`.
#. Once the beam is straight, slowly change the wavelength's :guilabel:`Offset` until the beam has an even thickness across the field of view.
#. Under :guilabel:`Waveform Parameter Settings`, press :guilabel:`Save Configuration`.
#. Under the :guilabel:`Channels` tab, restore the filter to its non-empty position.
#. Go to :guilabel:`Camera Settings` and ensure that "Light-Sheet" is selected under :guilabel:`Sensor Mode`. Slowly increase the wavelength's :guilabel:`Amplitude` until the beam becomes a straight line across the screen. If the beam does not become straighter, try changing the camera's :guilabel:`Readout Direction`.
#. If beam is diverges towards the ends of the camera, reduce the :guilabel:`Height` of camera under :guilabel:`Region of Interest Settings` tab by 10 pixels.
#. After optimal parameters are found, swap the spherical lens for the cylindrical lens.


Loading and finding the sample
------------------------------

#. Load the sample on the microscope.
#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Scroll around with the stage either via joystick or using the controls in the :guilabel:`Stage Control` tab until the sample comes into view.
#. If using the joystick to move to the stage into the correct position, press the :guilabel:`STOP` button under the :guilabel:`Stage Control` tab to update the stage positions in the software after moving the stage.
#. Set the resonant galvo :guilabel:`Galvo 0` to 0.3 to mitigate any striping artifacts during imaging.

.. z_stack:

Imaging a Z-Stack using Stop and Settle Mode
--------------------------------------------
#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Using the :guilabel:`Stage Control`, go to a shallow Z-position in the sample. Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)` press :guilabel:`Set Start Pos`.
#. Go to a deep Z-position in the sample. Press :guilabel:`Set End Pos`.
#. Make sure :guilabel:`Set Foc` is 0 for both the :guilabel:`Set Start Pos` and :guilabel:`End Pos`.
#. Type the desired step size (units um) in the :guilabel:`Step Size` dialog box  :guilabel:`Stack Acquistion Settings (um)`. Step size can only be increments of 0.1 (um) and the minimum is 0.2 (um).
#. Select the number of color channels needed imaging in the :guilabel:`Channel tab` under :guilabel: `Channel Settings`. Select the correct filter for each channel by using the dropdown menu after each channel under the :guilabel:`Filter`.
#. Change the exposure time by changing number in the :guilabel:`Exp. Time (ms)` for each channels. For the ORCA Lightning camera using ASLM mode, the minimum frame rate is 75 ms and the maximum is 100 ms.
#. Set :guilabel:`Interval` to be 1.0 for each channel.
#. Set :guilabel:`Defocus` to be 0 for each channel.
#. Select "Z-Stack" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`.
#. Enter the sample parameters in the :guilabel:`File Saving Dialog` that pops up. Press :guilabel:`Acquire Data`.

.. Constant Velocity Acquisition:

Imaging a Z-Stack using Constant Velocity Acquisition Mode
----------------------------------------------------------
#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Using the :guilabel:`Stage Control`, go to a shallow Z-position in the sample. Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)` press :guilabel:`Set Start Pos`.
#. Go to a deep Z-position in the sample. Press :guilabel:`Set End Pos`.
#. Make sure :guilabel:`Set Foc` is 0 for both the :guilabel:`Set Start Pos` and :guilabel:`End Pos`.
#. Type the desired step size (units um) in the :guilabel:`Step Size` dialog box  :guilabel:`Stack Acquistion Settings (um)`. Step size can only be increments of 0.1 (um) and the minimum is 0.2 (um).
#. Select the number of color channels needed imaging in the :guilabel:`Channel tab` under :guilabel: `Channel Settings`. Select the correct filter for each channel by using the dropdown menu after each channel under the :guilabel:`Filter`.
#. Change the exposure time by changing number in the :guilabel:`Exp. Time (ms)` for each channels. For the ORCA Lightning camera using ASLM mode, the minimum frame rate is 75 ms and the maximum is 100 ms.
#. Set :guilabel:`Interval` to be 1.0 for each channel.
#. Set :guilabel:`Defocus` to be 0 for each channel.
#. Select "Constant Velocity Acquisition" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`.
#. Enter the sample parameters in the :guilabel:`File Saving Dialog` that pops up. Make sure to save to SSD drive or change buffer size in configuration file to prevent any overwriting of images. Then Press :guilabel:`Acquire Data`.
#. To change frame buffer size, in the :guilabel:`CameraParameters` section in the :guilabel:`experiment.yaml` file in your local navigate directory in the :guilabel:`config` folder, change :guilabel:`databuffer_size` to desired number of frames. Make sure the size of the desired number of frames isn't above the available RAM in the computer.
