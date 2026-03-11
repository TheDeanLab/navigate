==================================
Signal-to-Noise Visualization Mode
==================================

.. _snr_mode:


Signal-to-noise ratio (SNR) visualization helps assess image quality in
real time. It is useful for microscope alignment and low-signal workflows.

Future releases will support direct acquisition of offset/variance maps from
within **navigate**. For now, generate these maps with camera-vendor software
or custom scripts.

Acquiring Offset And Variance Maps
----------------------------------

As a guideline, acquire data for offset/variance maps using an exposure time
similar to your imaging workflow.

1. **Capture dark frames.** Block incoming light and capture a stack of dark
   frames (for example, 1000 frames).
2. **Calculate the offset map.** Compute the minimum across dark frames.
3. **Calculate the variance map.** Compute the variance across dark frames.
4. **Save both maps.** Save offset/variance images as TIFF files in a
   ``camera_maps`` folder under the **navigate** home directory.

   - Windows: ``C:\Users\<username>\AppData\Local\.navigate\camera_maps\``
   - macOS/Linux: ``~/.navigate/camera_maps/``
   - Filenames:
     ``<camera_serial_number>_off.tiff`` and
     ``<camera_serial_number>_var.tiff``

5. Launch **navigate**. On startup, **navigate** detects available maps in the
   configured directory and exposes SNR visualization options for that camera.
