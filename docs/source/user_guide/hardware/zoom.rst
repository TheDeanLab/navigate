===============
Mechanical Zoom
===============

Zoom devices control the magnification of the microscope. If such control is not
needed, the software expects a :ref:`Synthetic Zoom <synthetic_zoom>` to provide
the fixed magnification and the effective pixel size of the microscope.

---------------

Dynamixel
---------

MX-28R
~~~~~~

This software supports the
`Dynamixel Smart Actuator <https://www.dynamixel.com/>`_.

.. note::

    The ``positions`` specify the voltage of the actuator at different zoom positions.
    The ``stage_positions`` account for focal shifts in between the different zoom values
    (the MVXPLAPO does not have a consistent focal plane). These may change depending on
    the immersion media. Here it is specified for a ``BABB`` (Benzyl Alcohol Benzyl
    Benzoate) immersion media.  The ``pixel_size`` specifies the effective pixel size of
    the system at each zoom.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            zoom:
              hardware:
                type: DynamixelZoom
                servo_id: 1
                port: COM1
                baudrate: 9600
              position:
                1x: 200.0
                6.5x: 2000.0
              pixel_size:
                1x: 6.5
                6.5x: 1.0
              stage_positions:
                BABB:
                  f:
                    36X: 0


|

---------------

.. _synthetic_zoom:

Synthetic Zoom
--------------

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            zoom:
              hardware:
                type: synthetic
                servo_id: 1
                port: COM1
                baudrate: 9600
              position:
                1x: 200.0
                6.5x: 2000.0
              pixel_size:
                1x: 6.5
                6.5x: 1.0
              stage_positions:
                BABB:
                  f:
                    36X: 0

|
