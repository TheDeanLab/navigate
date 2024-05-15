
.. _hardware_overview:

##################
Supported Hardware
##################


**navigate** provides access to a growing list of hardware devices. Information on how to
configure each of these devices is provided :doc:`here <hardware/hardware_home>`.


.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - **Equipment**
     - **Devices**
   * - *Cameras*
     -
        * Hamamatsu Orca Flash 4.0.
        * Hamamatsu Orca Fusion.
        * Hamamatsu Orca Fire.
        * Hamamatsu Orca Lightning.
        * Photometrics Iris15
   * - *Deformable Mirrors*
     -
        * Imagine Optics
   * - *Filter Wheel*
     -
        * ASI with Tiger Controller
        * Sutter Lambda 10-3
        * Sutter Lambda LS
   * - *Galvanometers*
     -
        * Analog controlled devices.
   * - *Lasers*
     -
        * Analog, Digital, and Mixed Modulation modes.
   * - *Remote Focusing Devices*
     -
        * Analog controlled voice coils, electro-tunable lens, etc.
        * Equipment Solutions LFA2004 with hybrid RS232 and analog control.
   * - *Stages*
     -
        * Analog controlled galvanometers and piezoelectric stages.
        * ASI with Tiger Controller
        * ASI with MFC2000 Controller
        * Mad City Labs Nano-Drive
        * Physik Instrumente
        * Sutter MP285
        * Thorlabs Stepper Actuators with a KST101 K-Cube Controller.
        * Thorlabs Piezoelectric Inertia Actuators with a KIM001 K-Cube Controller
   * - *Shutters*
     -
        * Digitally controlled shutters.
   * - *Zoom*
     -
        * Dynamixel MX-28R


Device Firmware
===============

.. _firmware_overview:


**navigate** has been tested with the following firmware. Devices that are controlled
with analog or digital voltages are omitted.


.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - **Manufacturer**
     - **Firmware Version**
   * - *ASI*
     -
        * Tiger Controller 2.2.0.

   * - *Dynamixel*
     -
        * Dynamixel MX-28R

   * - *National Instruments*
     -
        * NI-DAQmx Device Drivers: 22.5.0, 22.8.0, 23.3.0, 23.8.0

   * - *Hamamatsu*
     -
        * DCAM API: 20.7.641, 21.7.4321, 22.9.6509, 22.11.4321, 23.12.6736
        * Camera Firmware: 2.21B, 2.53.A, 3.20.A, 4.30.B,
        * Active Silicon CoaXpress: 1.10, 1.13, 1.21.

   * - *Photometrics*
     -
        * PVCAM: 3.9.13

   * - *Physik Instrumente*
     -
        * PIMikroMove: 2.36.1.0
        * PI_GCS2_DLL: 3.22.0.0
