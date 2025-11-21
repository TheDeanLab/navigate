==================================
Signal-to-Noise Visualization Mode
==================================

The Signal-to-Noise Ratio (SNR) Visualization Mode is designed to help users assess the quality of their images by visualizing the signal-to-noise ratio in real-time. This mode is particularly useful for identifying areas of high and low signal quality, which is helpful when aligning a microscope or when working with low-light conditions.

In the future, we will provide a method to acquire the offset and variance maps directly from within *navigate*. For now, users will need to provide these maps manually using commercial software provided by the camera manufacturer or by using custom scripts.

-------------------------------

Acquiring Offset and Variance Maps
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In general, it is a good idea to acquire the data used to derive the offset and variance maps at a similar exposure time as the one used for imaging. To calculate the offset and variance maps, users can follow these general steps:

1. **Capture Dark Frames**: With the camera lens cap on, capture a series of dark frames (e.g., 1000 frames). These frames will be used to calculate the offset map.

2. **Calculate the Offset Map**: Compute the minimum of the dark frames to create the offset map. This map represents the baseline signal level of the camera.

3. **Calculate the Variance Map**: Compute the variance of the dark frames to create the variance map. This map represents the noise characteristics of the camera.

4. **Save the Maps**: Save the offset and variance maps as tiff images in a folder titled `camera_maps` in navigate's home directory.

    - For Windows-based users: ``C:\AppData\Local\.navigate\camera_maps\``.
    - For Linux and MacOS users: ``/home/<username>/.navigate/camera_maps/``.
    - The files should be named as ``<camera_serial_number>_off.tiff`` and ``<camera_serial_number>_var.tiff``, where ``<camera_serial_number>`` is the serial number of the camera being used. By providing the serial number, users can easily switch between different cameras without needing to reconfigure the settings each time.

5. **Launch navigate**: Next time you launch **navigate**, it will automatically detect the presence of the offset and variance maps in the specified directory and provide the appropriate options to enable the SNR visualization mode.