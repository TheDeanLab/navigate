Adding New Hardware
=========================

ASLM is built with an abstraction layer that enables operation with a diverse set of
hardware manufacturers and equipment.

Hardware Classes
--------------

- Cameras
    * Hamamatsu Flash 4.0, Fusion, etc.
    * Photometrics - In Progress
- Deformable Mirrors
    * Imagine Optics - In Progress
- Data Acquisition Cards
    * National Instruments
- Filter Wheels
    * Sutter
- Galvanometers
- Lasers
    * Coherent OBIS
    * Omicron LuxX
- Remote Focusing Devices
    * Equipment Solutions
- Shutters
- Stages
    * Physik Instrumente
    * Sutter MP-285 - In Progress
    * Galvo Scanning
- Zoom
    * Dynamixel

Scientific Units
----------------
Deviations from this can occur where it is necessary to pass a different unit to a
piece of hardware.

* Time - Milliseconds
* Distance - Micrometers


How to Add New Hardware
-----------------------
Each hardware class is accompanied by a base class, and a synthetic class.

Here we will provide an example of how to contribute a new piece of hardware.  Will
use the Sutter MP-285 stage as an example.
