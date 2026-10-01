.. _acquire_mesospimbt:

========================
Imaging on a mesoSPIM BT
========================

This is a case study in using the software to image with a `mesoSPIM BT microscope <https://pubmed.ncbi.nlm.nih.gov/38538644/>`_. It is a Digitally Scanned, Axially Swept Light-Sheet Microscope that scans the beam laterally (``X``) with galvanometric mirrors to create a virtual sheet of light, and axially (``Y``) with an electronically tunable lens. The sample is moved in the detection direction (``Z``) to acquire a stack. Tiling in ``X``, ``Y``, and ``Z`` is provided by a motorized stage.

.. note::

   Interface illustrations use the current night theme with example microscope
   settings. Follow the values and adjustments in the instructions for your
   microscope. The beam, tissue, and autofocus plots below are preserved from
   the original case study, cropped to remove the historical interface.

-----------------

Setting the beam parameters
===========================

Make sure the imaging chamber is empty or, if a sample is mounted, the sample is not in the beam path.

#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Go to the :guilabel:`Channels` tab. Choose the wavelength you want to align. Set the laser's :guilabel:`Power` to ``100.0``. Change :guilabel:`Filter` to an "Empty" option.

   .. image:: ../../images/channel-selector.png
      :alt: Channel selection, illumination power, filter, and exposure controls.

#. Go to the :menuselection:`Microscope Configuration --> Waveform Parameters`. A popup named :guilabel:`Waveform Parameter Settings` will appear. Make sure the :guilabel:`Mode` matches "mesoSPIM BT" and the :guilabel:`Magnification` matches the magnification of the objective you are using.

.. note::

    The :guilabel:`Mode` is the name of the microscope as defined in the ``configuration.yaml`` file. Likewise, the :guilabel:`Magnification` is the magnification(s) for that microscope as defined in the ``configuration.yaml`` file.

    The mesoSPIM BT largely operates at a fixed magnification. However, the original mesoSPIM used a variable magnification research grade macro zoom microscope.

#. :guilabel:`Galvo 0` digitally sweeps the beam across the field of view in the ``X`` direction. To align the axially-swept light sheet parameters, set the :guilabel:`Galvo 0` :guilabel:`Amplitude` to ``0.0``.

   .. image:: ../../images/popup_waveform_parameters.png
      :alt: Waveform settings for illumination and galvo controls.

#. The empty filter makes us susceptible to seeing particles scattering light in the chamber. This can affect the software's autoscaling routine. To ensure we are looking at the beam correctly, uncheck :guilabel:`Autoscale` and set the :guilabel:`Min Counts` and :guilabel:`Max Counts` so the beam is visible, but not saturating the display.

#. Set the wavelength's :guilabel:`Amplitude` to ``0.0``. Set the wavelength's :guilabel:`Offset` so that the beam is focused in the center of the field of view.

   .. image:: ../../images/case-studies/meso-beam-4.png
      :alt: Original beam image before galvo centering.

#. Set the :guilabel:`Galvo 0` :guilabel:`Offset` so that the beam is centered in the field of view. Click the :guilabel:`Camera View` to toggle the crosshair, which indicate the center of the field of view.

   .. image:: ../../images/case-studies/meso-beam-6.png
      :alt: Original beam centered on the camera crosshair.

#. Go to :guilabel:`Camera Settings` and ensure that :guilabel:`Light-Sheet` is selected under :guilabel:`Sensor Mode`. Slowly increase the wavelength's :guilabel:`Amplitude` until the beam becomes a straight line across the screen. If the beam does not become straighter, try changing the camera's :ref:`Readout Direction <ui_camera_modes>`.

   .. image:: ../../images/case-studies/meso-beam-8.png
      :alt: Original beam after adjusting the light-sheet sweep amplitude.

   Adjust the :guilabel:`F` (focus) value in the :guilabel:`Stage Control` panel until the beam is as thin/focused as possible.

   .. image:: ../../images/case-studies/meso-beam-9.png
      :alt: Original beam after focus adjustment.

#. Once the beam is straight, slowly change the wavelength's :guilabel:`Offset` until the beam has an even thickness across the field of view. This will also make the beam a bit thinner.

   .. image:: ../../images/case-studies/meso-beam-11.png
      :alt: Original beam after adjusting sweep offset for uniform thickness.

.. warning::

    Proper alignment of the ASLM scan is critical to the quality of the image. We recommend iterating the :guilabel:`Amplitude`, :guilabel:`Offset`, and :guilabel:`F` until the beam is uniformly as thin as possible throughout the entire field of view.

#. Slowly increase :guilabel:`Galvo 0`'s :guilabel:`Amplitude` until the entire field of view is just covered by the digitally scanned beam. Over-scanning the beam will result in a loss of light, but also provide a more uniform illumination for tiling applications.

   .. image:: ../../images/case-studies/meso-beam-13.png
      :alt: Original sheet after increasing the lateral galvo sweep.

   .. image:: ../../images/case-studies/meso-beam-15.png
      :alt: Original sheet covering the field of view.

#. Under :guilabel:`Waveform Parameter Settings`, press :guilabel:`Save Configuration`.
#. Under the :guilabel:`Channels` tab, restore the filter to its non-empty position.

-----------------

Loading and finding the sample
==============================

#. Load the sample on the microscope.
#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Scroll around with the stage either via joystick or using the controls in the :guilabel:`Stage Control` tab until the sample comes into view.

   .. image:: ../../images/case-studies/find-sample.png
      :alt: Original tissue image during sample positioning.

#. Focus on the sample using the ``F`` axis. Optionally, use Autofocus by going to :menuselection:`Autofocus --> Autofocus Settings`. Press :guilabel:`Autofocus`. Ensure there is a clear peak in the resulting plot.

   .. image:: ../../images/popup_autofocus_settings.png
      :alt: Current autofocus controls.

   .. image:: ../../images/case-studies/autofocus-settings-plot.png
      :alt: Original autofocus curve with a clear focus peak.

   If there is not a clear peak, the autofocusing routine did not work. Try increasing the laser power and/or bringing the sample more into focus manually. If it did work, the sample should now be in focus.

   .. image:: ../../images/case-studies/autofocus-image.png
      :alt: Original tissue image after autofocus.

   .. note::

        Sometimes there isn't a clear peak, but there is a clear trend toward a peak. In this case, the autofocus is converging, but the true focus position is outside the range of your search. Run autofocus again to achieve convergence.

        .. image:: ../../images/case-studies/autofocus-settings-partial-plot.png
           :alt: Original autofocus curve with the peak outside the search range.

-----------------

.. _z_stack_mesospim:

Imaging a z-stack
=================

#. Select "Continuous Scan" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`. This will launch a live acquisition mode.
#. Using the :guilabel:`Stage Control`, go to a shallow Z-position in the sample. Under the :guilabel:`Channels` tab, in :guilabel:`Stack Acquisition Settings (um)` press :guilabel:`Set Start Pos/Foc`.

   .. image:: ../../images/press-start-pos.png
      :alt: Stack acquisition controls after setting the start position.

#. Go to a deep Z-position in the sample. Press :guilabel:`Set End Pos/Foc`.

   .. image:: ../../images/press-end-pos.png
      :alt: Stack acquisition controls after setting the end position.

#. Select "Z-Stack" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`.
#. Enter the sample parameters in the :guilabel:`File Saving Dialog` that pops up. Press :guilabel:`Acquire Data`.

   .. image:: ../../images/save-dialog-box.png
      :alt: Acquisition file saving dialog.

-----------------

.. _acquire_mesospimbt_tiling:

Tiling a sample larger than the field of view
=============================================

This assumes you have already set the start and end positions in :guilabel:`Stack Acquisition Settings (um)` (see :ref:`Imaging a Z-Stack <i_want_to_z_stack>`).

#. Under the :guilabel:`Channels` tab, press :guilabel:`Launch Tiling Wizard`.

   .. image:: ../../images/popup_tiling_wizard.png
      :alt: Tiling wizard with axis bounds and multiposition table controls.

#. Go to thickest part of the sample. Go to the lower bound of the ``X`` axis and press :guilabel:`Set X Start`. Go to the upper bound of the ``X`` axis and press :guilabel:`Set X End`. Repeat for all axes except for focus.
#. Ensure the sample is in focus and press :guilabel:`Set F Start` and :guilabel:`Set F End` without changing the focus position.
#. Press :guilabel:`Populate Multi-Position Table`. Navigate to the :guilabel:`Multiposition` tab and ensure the locations populated.

   .. image:: ../../images/MultiPositionTab.png
      :alt: Multiposition table with example stage coordinates.

#. Under the :guilabel:`Channels`, make sure :guilabel:`Enable` is checked under :guilabel:`Multi-Position Acquisition`.
#. Under the :guilabel:`Channels`, make sure :guilabel:`Save Data` is checked under :guilabel:`Timepoint Settings`.
#. Select "Z-Stack" from the dropdown next to the :guilabel:`Acquire` button. Press :guilabel:`Acquire`.
#. Enter the sample parameters in the :guilabel:`File Saving Dialog` that pops up. Press :guilabel:`Acquire Data`.
