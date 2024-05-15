========
Shutters
========

When controlled with analog, digital, or mixed modulation, not all laser sources
reduce their emitted intensity to 0. In such cases, residual illumination subjects
the specimen to unnecessary irradiation between image acquisitions. Shutters overcome
this by completely blocking the laser, albeit on a much slower timescale than direct
modulation of the laser. With **navigate**, shutters automatically open at the start
of acquisition and close upon finish.

------------

Analog/Digital-Controlled Shutters
----------------------------------

Thorlabs shutters are controlled via a digital on off voltage.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            shutter:
              hardware:
                type: NI
                channel: PXI6249/port0/line0
                min: 0.0
                max: 5.0

|

------------------

Synthetic Shutter
-----------------
If no shutter is present, one must configure the software to use a synthetic
shutter.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            shutter:
              hardware:
                type: synthetic
                channel: PXI6249/port0/line0
                min: 0.0
                max: 5.0

|
