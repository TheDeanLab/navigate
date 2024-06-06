=============
Filter Wheels
=============

Filter wheels can be used in both illumination and detection paths. Dichroic
turrets are controlled via the same code as filter wheels. The user is expected to
change the names of available filters to match what is in the filter wheel or turret.

-----------

Sutter Instruments
------------------

Lambda 10-3 & 10-B
~~~~~~~~~~~~~~~~~~

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

FW-1000
~~~~~~~

The ASI `filter wheel <https://www.asiimaging
.com/illumination-control/fw-1000-high-speed-filter-wheel/>`_ is controlled by the
ASI Tiger Controller. Thus, you should provide the same ``comport`` entry as you did
for the stage. A single communication instance is used for both the stage and filter wheel.

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

LUDL Electronic Products
------------------

MAC6000
~~~~~~~

.. note::
    Currently, the software only supports a single filter wheel for the MAC6000
    device. Should additional filter wheels be necessary, please reach out to the
    **navigate** team by placing a feature request on GitHub.


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            filter_wheel:
              hardware:
                type: LUDLFilterWheel
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

Analog/Digital Devices
------------------

Some manufacturers provide filter wheels that are controlled by analog or digital signals.
Here, each digital signal corresponds to a filter position. The user must specify the
number of filters in the filter wheel and the digital signal that corresponds to each
filter position.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            filter_wheel:
              hardware:
                type: NI
                wheel_number: 1
              filter_wheel_delay: 0.050
              available_filters:
                473nm: Dev2/port0/line1
                561nm: Dev2/port0/line3
                638nm: Dev2/port0/line5
                Empty: Dev2/port0/line7

|

-------------

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
