=======================
Remote Focusing Devices
=======================

Voice coils, also known as linear actuators, play a crucial role in implementing
aberration-free remote focusing in **navigate**. These electromagnetic actuators are
used to control the axial position of the light-sheet and the sample relative to the
microscope objective lens. By precisely adjusting the axial position, the focal plane
can be shifted without moving the objective lens, thus enabling remote focusing.

Focus tunable lenses serve as an alternative to voice coils owing to their simple
operation and high bandwidth. Tunable lenses axially scan
a beam by introducing defocus into the optical train. Nonetheless, they do not provide the
higher-order correction provided by voice coils in an aberration-free remote focusing system.

--------------

Equipment Solutions
-------------------

LFA-2010
~~~~~~~~

Configuration of the device can be variable. Many voice coils we have received require
establishing serial communication with the device to explicitly place it in an analog
control mode. In this case, the comport must be specified properly in the configuration
file.

More recently, Equipment Solutions has begun delivering devices that
automatically initialize in an analog control mode, and thus no longer need the
serial communication to be established. For these devices, we recommend using the analog
control mode described in the next section.

The `LFA-2010 Linear Focus Actuator <https://www.equipsolutions.com/products/linear-focus-actuators/lfa-2010-linear-focus-actuator/>`_
is controlled with a `SCA814 Linear Servo Controller <https://www.equipsolutions.com/products/linear-servo-controllers/sca814-linear-servo-controller/>`_,
which accepts a +/- 2.5 Volt analog signal. The minimum and maximum voltages can be set
in the configuration file to prevent the device from receiving a voltage outside of its
operating range.


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            remote_focus_device:
              hardware:
                type: EquipmentSolutions
                channel: PXI6269/ao3
                min: -5.0
                max: 5.0
                comport: COM2
                baudrate: 9600

|

-------------

Analog Controlled Voice Coils and Tunable Lenses
------------------------------------------------

In principle, this hardware type can support any analog-controlled voice coil or tunable lens.
The `BLINK <https://www.thorlabs.com/thorproduct.cfm?partnumber=BLINK>`_ and the
`Optotune Focus Tunable Lens <https://www.optotune.com/tunable-lenses>`_ are
controlled with an analog signal from the DAQ.

Thorlabs BLINK
~~~~~~~~~~~~~~
The BLINK is a voice coil that is
pneumatically actuated voice coil. It is recommended that you specify the min and max
voltages that are compatible with your device to prevent the device from receiving a
voltage outside of its operating range.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            remote_focus_device:
              hardware:
                type: NI
                channel: PXI6269/ao3
                min: -5.0
                max: 5.0
                comport: COM2
                baudrate: 9600

|

Optotune Focus Tunable Lens
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            remote_focus_device:
              hardware:
                type: NI
                channel: PXI6269/ao3
                min: -5.0
                max: 5.0
                comport: COM2
                baudrate: 9600

|

------------------

Synthetic Remote Focus Device
-----------------------------
If no remote focus device is present, one must configure the software to use a synthetic
remote focus device.

.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
          remote_focus_device:
              hardware:
                type: synthetic
                channel: PXI6269/ao3
                min: -5.0
                max: 5.0
                comport: COM2
                baudrate: 9600

|
