========================================
Imaging on the CT-ASLM-V1 and CT-ASLM-V2
========================================

This is a case study in using the software to image with a
`CT-ASLM-V1 and CT-ASLM-V2 microscopes <https://www.nature.com/articles/s41592-019-0615-4>`_.

-----------------

Setting up the chamber
======================

Make sure the chamber is clean and dry. If in doubt, fill the chamber with deionized water to see
if there is any residue. To clean the chamber, rinse it with deionized water and ethanol, then
gently clean the chamber with Q-tips. Repeat the process a few times and end the
process with a rinse of 100% ethanol. Gently clean the objectives with lens paper and
100% ethanol. Finally, let the chamber air dry. To speed up the drying process, one
can gently blow some air into the chamber.

Once the chamber is completely dry, fill the chamber with imaging media.


-----------------

Sample loading and finding the samples
======================================

It's recommended to start the software before loading the sample on the stage.

#. Mount the sample on custom cut glass slide with silicon or super glue.
#. Mount the glass slide onto the sample holder.
#. Mount the sample holder onto the stage with the sample facing the illumination and
   detection objective so the glass slide is 45 degrees with both objectives.
#. Put down the slit out of the setup.
#. Go to :guilabel:`Camera Settings`. Select "Normal" under :guilabel:`Sensor Mode`.
#. Go to the :menuselection:`Microscope Configuration --> Waveform Parameters`. A popup
   named :guilabel:`Waveform Parameter Settings` will appear.
#. Set the wavelength's :guilabel:`Amplitude` and :guilabel:`Offset` to ``0.0``.
#. Select the channel with a proper laser under the :guilabel:`Channels` tab and set
   the laser power to an appropriate value.
#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Scroll around with the stage either via joystick or using the controls in the
   :guilabel:`Stage Control` tab until the sample comes into view.
#. Focus on the sample in the center of the beam. Zoom in by scrolling the mouse.
   Slowly adjusting the focus by scrolling the piezo controller to move the
   detection objective along the z axis. Lower the laser power if the image is
   saturated.


-----------------

.. _z_stack_stelzer:

Imaging a Z-Stack with Stelzer mode
===================================

Stelzer mode is the normal non-ASLM light sheet mode, it gives more signal while
offering around 1040 nm (CT-ASLM-V1) and 500 nm (CT-ASLM-V2) lateral resolution.

#. Go to the :menuselection:`Microscope Configuration --> Waveform Parameters`. A popup
   named :guilabel:`Waveform Parameter Settings` will appear.
#. Set the wavelength's :guilabel:`Amplitude` and :guilabel:`Offset` to ``0.0``.
#. Go to :guilabel:`Camera Settings`, select "Normal" under :guilabel:`Sensor Mode`.
#. Put a slit into the setup.
#. Select the channel with a proper laser under the :guilabel:`Channels` tab and set
   the laser power to an appropriate value.
#. Select :guilabel:`Continuous Scan` from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. If needed, slowly adjust the slit opening until the image sharpness looks uniform
   across the whole field of view. Uncheck :guilabel:`Autoscale` in
   :guilabel:`Camera View` under LUT and adjust the :guilabel:`Min Counts` and
   :guilabel:`Max Counts` if needed.
#. Go to :guilabel:`Stage Control`, set the Z position in :guilabel:`Stage Positions`
   to be ``0``.
#. Find the region of interest by using the joystick or using the controls in the
   :guilabel:`Stage Control` tab.
#. Move along the Z axis with the joystick or the "Focus" in the
   :guilabel:`Stage Control` tab to one end of the region of interest. Under the
   :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)`, press
   :guilabel:`Set Start Pos/Foc`.
#. Go to :guilabel:`Stage Control`, change the Z position in
   :guilabel:`Stage Positions` to set the scan range. Be aware the range for z-piezo
   is 0 - 200. Going outside of the range will cause the stage to have issues.
#. Go back to :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)`,
   press :guilabel:`Set End Pos/Foc`.
#. Setup :guilabel:`Step Size` under the :guilabel:`Channels`, recommend 3.0
   (CT-ASLM-V1) and 1.0 (CT-ASLM-V2).
#. Under the :guilabel:`Channels`, make sure :guilabel:`Enable` is unchecked under
   :guilabel:`Multi-Position Acquisition`.
#. Under the :guilabel:`Channels`, make sure :guilabel:`Save Data` is checked under
   :guilabel:`Timepoint Settings`.
#. Select "Z-Stack" from the dropdown next to the :guilabel:`Acquire` button. Press
   :guilabel:`Acquire`. A popup named :guilabel:`File Saving Dialog` will appear.
#. Fill out the fields and press :guilabel:`Acquire Data`.

-----------------

.. _z_stack_aslm:

Imaging a Z-Stack with ASLM mode
================================

ASLM mode is the high-resolution light sheet mode, it gives leas signal but offering
around 950 nm (CT-ASLM-V1) and 480 nm (CT-ASLM-V2) isotropic resolution.

#. Switch the slit out of the setup.
#. Go to :guilabel:`Camera Settings`, select "Light-Sheet" under
   :guilabel:`Sensor Mode`.
#. Select the channel with a proper laser under the :guilabel:`Channels` tab and set
   the laser power to an appropriate value.
#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button.
   Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Go to the :menuselection:`Microscope Configuration --> Waveform Parameters`. A popup
   named :guilabel:`Waveform Parameter Settings` will appear.
#. Uncheck :guilabel:`Autoscale` in :guilabel:`Camera View` under LUT and adjust the
   :guilabel:`Min Counts` and :guilabel:`Max Counts` if needed.
#. Set the wavelength's :guilabel:`Amplitude` to ``0.0``.
#. Adjust the wavelength's :guilabel:`Offset` so the focus part of the image can be
   located perfectly in the center of the field of view.
#. Slowly adjust the wavelength's :guilabel:`Amplitude` so it will be uniform across
   the whole field of view.
#. Adjust the wavelength's :guilabel:`Offset` again slightly and make sure it is
   uniformly in focus across the whole field of view.
#. Go to :guilabel:`Stage Control`, set the Z position in :guilabel:`Stage Positions`
   to be ``0``.
#. Find the region of interest by using the joystick or using the controls in the
   :guilabel:`Stage Control` tab.
#. Move along the Z axis with the joystick or the “Focus” in the
   :guilabel:`Stage Control` tab to one end of the region of interest. Under the
   :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)`, press
   :guilabel:`Set Start Pos/Foc`.
#. Go to :guilabel:`Stage Control`, change the Z position in
   :guilabel:`Stage Positions` to set the scan range. Be aware the range for z-piezo is
   0 - 200. Going outside of the range will cause the stage to have issues.
#. Go back to :guilabel:`Channels` tab, in :guilabel:`Stack Acquistion Settings (um)`,
   press :guilabel:`Set End Pos/Foc`.
#. Setup :guilabel:`Step Size` under the :guilabel:`Channels`, recommend 0.46
   (CT-ASLM-V1) and 0.2 (CT-ASLM-V2) for isotropic imaging.
#. Under the :guilabel:`Channels`, make sure :guilabel:`Enable` is unchecked under
   :guilabel:`Multi-Position Acquisition`.
#. Under the :guilabel:`Channels`, make sure :guilabel:`Save Data` is checked under
   :guilabel:`Timepoint Settings`.
#. Select "Z-Stack" from the dropdown next to the :guilabel:`Acquire` button. Press
   :guilabel:`Acquire`. A popup named :guilabel:`File Saving Dialog` will appear.
#. Fill out the fields and press :guilabel:`Acquire Data`.


-----------------

Tiling a sample larger than the field of view
=============================================

This assumes you have already found the samples and ready to acquire data in either
Stelzer mode or ASLM mode. (see
:ref:`Imaging a Z-Stack with Stelzer mode <z_stack_stelzer>` and
:ref:`Imaging a Z-Stack with ASLM mode <z_stack_aslm>`).

#. Under :guilabel:`Channels` tab, press :guilabel:`Launch Tiling Wizard`. A popup
   named :guilabel:`Multi-Position Tiling Wizard` will appear.
#. Follow :ref:`Imaging a Z-Stack with Stelzer mode <z_stack_stelzer>` to set up the
   start and end positions in :guilabel:`Stack Acquistion Settings (um)`. At the same
   time, when pressing :guilabel:`Set Start Pos/Foc` to set up the start position, go
   to :guilabel:`Multi-Position Tiling Wizard` and press :guilabel:`Set Z Start`. When
   pressing :guilabel:`Set End Pos/Foc` to set up the end position, go to
   :guilabel:`Multi-Position Tiling Wizard` and press :guilabel:`Set Z End`.
#. Move the joystick or the “X Movement” in the :guilabel:`Stage Control` tab to the
   lower bound of the x-axis and press :guilabel:`Set X Start` in the
   :guilabel:`Multi-PositionTiling Wizard` popup. Navigate to the upper bound of the
   x-axis and press :guilabel:`Set X End` in the
   :guilabel:`Multi-Position Tiling Wizard` popup. Repeat for all axes except for z.
#. Press :guilabel:`Populate Multi-Position Table`. Navigate to the
   :guilabel:`Multiposition` tab and ensure the locations populated.
#. Under the :guilabel:`Channels`, make sure Enable is checked under
   :guilabel:`Multi-Position Acquisition`.
#. Under the :guilabel:`Channels`, make sure :guilabel:`Save Data` is checked under
   :guilabel:`Timepoint Settings`.
#. Select “Z-Stack” from the dropdown next to the :guilabel:`Acquire` button. Press
   :guilabel:`Acquire`.
#. Enter the sample parameters in the :guilabel:`File Saving Dialog` that pops up.
   Press :guilabel:`Acquire Data`.
