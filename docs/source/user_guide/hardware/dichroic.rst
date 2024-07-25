================
Dichroic Turrets
================

Dichroics can be used to reflect the excitation light towards the camera, while
permitting the emission light that is captured by the objective to be transmitted
to the camera. Alternatively, they can be placed in the detection path to separate
different emission wavelengths and to direct it to the appropriate camera.

Currently, **navigate** incorporates a dichroic turret as a filter wheel, which enables
you to add as many different dichroic turrets as you would like.

.. note::

    The `name` parameter under `hardware` is optional. If not provided, the name of the
    device will be default to Filter 0, Filter 1, ... Filter N in the GUI. However, if
    is is provided, then the GUI will automatically use the name provided as a label.

ASI
---

C60-CUBE-SLDR
~~~~~~~~~~~~~

The `C60-CUBE-SLDR <https://www.asiimaging.com/illumination-control/c60-cube-sldr/>`_
is a motorized dichroic slider that can be controlled by the ASI Tiger Controller.
The example below shows the configuration file with one dichroic turret, and one
filter wheel. The same communication instance is used for both the stage and filter
wheel. It holds a maximum of 4 dichroics.


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          -
            filter_wheel:
              hardware:
                type: ASI
                name: Filter Wheel 1
                wheel_number: 1
                port: COM1
                baudrate: 115200
              filter_wheel_delay: 0.03
              available_filters:
                Empty-Alignment: 0
                GFP: 1
                RFP: 2
                Far-Red: 3
          -
            filter_wheel:
              hardware:
                type: ASICubeSlider
                name: Dichroic Turret 1
                wheel_number: 2
                port: COM1
                baudrate: 115200
              filter_wheel_delay: 0.25
              available_filters:
                510LP: 0
                560LP: 1
                600LP: 2
                660LP: 3
|
