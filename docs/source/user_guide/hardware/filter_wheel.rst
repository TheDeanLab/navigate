=============
Filter Wheels
=============

Filter wheels can be used in both illumination and detection paths. Dichroic
turrets are controlled via the same code as filter wheels. The user is expected to
change the names of available filters to match what is in the filter wheel or turret.

-----------

Sutter Instruments
------------------
We typically communicate with Sutter Lambda 10-3 controllers via serial port. It is
recommended that you first establish communication with the device using manufacturer
provided software. Alternatively, one can use MicroManager. For some filter wheel types,
the filter_wheel_delay is calculated according to the size of the move and model of the
filter wheel. For other filter wheel types, the filter_wheel_delay is a fixed value, which is specified as
the ``filter_wheel_delay`` entry in the configuration file. The number of filter wheels
connected to the controller is specified as ``wheel_number`` in the configuration file.
Currently, both wheels are moved to the same position, but future implementations will
enable control of both filter wheels independently.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            filter_wheel:
              hardware:
                type: SutterFilterWheel
                wheel_number: 1
                port: COM1
                baudrate: 9600
              filter_wheel_delay: 0.03
              available_filters:
                Empty-Alignment: 0
                GFP: 1
                RFP: 2
                Far-Red: 3

|

-------------

ASI
---
The ASI filter wheel is controlled by the ASI Tiger Controller. Thus, you should provide the same
``comport`` entry as you did for the stage. A single communication instance is used for both the stage and filter wheel.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            filter_wheel:
              hardware:
                type: ASI
                wheel_number: 1
                port: COM1
                baudrate: 9600
              filter_wheel_delay: 0.03
              available_filters:
                Empty-Alignment: 0
                GFP: 1
                RFP: 2
                Far-Red: 3

|

--------------

Synthetic Filter Wheel
----------------------
If no filter wheel is present, one must configure the software to use a synthetic
filter wheel.


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            filter_wheel:
              hardware:
                type: synthetic
                wheel_number: 1
                port: COM1
                baudrate: 9600
              filter_wheel_delay: 0.03
              available_filters:
                Empty-Alignment: 0
                GFP: 1
                RFP: 2
                Far-Red: 3

|
