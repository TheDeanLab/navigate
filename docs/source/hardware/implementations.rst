==========================
Microscope Implementations
==========================

Multiscale Microscope
=====================

- Laser source - Omicron LightHUB Ultra. Requires ACC operating mode with analog modulation enabled for 488 nm and 642 nm lasers. 561, which operates separately, requires the mixed modulation mode (Obis).
- Stage - PI L-509.20DG10. Has a unidirectional repeatability of 100 nm, bidirectional repeatablility of 2 microns, and a minimum incremental motion of 100 nm. This is borderline too coarse.
- Camera - 2x Hamamatsu Flash 4.0 with frame grabbers
- Remote Focusing Units - Optotune Electrotunable Lens for low-resolution imaging
- Remote Focusing Unit - Equipment Solutions LFA-2004 for high-resolution imaging
- National Instruments PXIe-1073 Chassis equipped with PXI6733 and PXI6259 Data Acquisition Devices
- Filter Wheels - 2x 32mm High-Speed Filter Wheels from Sutter
- Objective Positioner - PI P726.1CD

.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_multiscale.yaml
       :language: yaml


|

Expansion ASLM
==============

- Laser source - Omicron LightHUB Ultra. Requires ACC operating mode with analog modulation enabled for 488 nm and 642 nm lasers. 561, which operates separately, requires the mixed modulation mode (Obis).
- Remote Focusing Unit - ThorLabs BLINK for high-resolution imaging
- Camera - Hamamatsu Lightning with frame grabbers
- Camera - Photometrics
- Filter Wheel - ASI
- Stage - ASI Tiger Controller

.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_upright.yaml
       :language: yaml

|

OPM-V2
======

- Laser source - Omicron LightHUB Ultra. Requires ACC operating mode with analog modulation enabled for 488 nm and 642 nm lasers. 561, which operates separately, requires the mixed modulation mode (Obis).
- Camera - Hamamatsu Flash 4.0 with frame grabbers.

.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_OPMv2.yaml
       :language: yaml

|

OPM-V3
======

- Laser source
- VAST

.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_OPMv3.yaml
       :language: yaml

|

CT-ASLM-V1
==========

- Laser source - Omicron LightHUB Ultra. Requires ACC operating mode with analog modulation enabled for 488 nm and 642 nm lasers. 561, which operates separately, requires the mixed modulation mode (Obis).
- Camera - Hamamatsu Flash 4.0 with frame grabbers.

CT-ASLM-V2
==========

- Laser source - Coherent OBIS 488, 561, and 647 nm
- Camera - Hamamatsu Flash 4.0 with frame grabbers
- Filter Wheel - Sutter Lambda 10-3
- Stages - Sutter MP285 and PiezoJena 200 Micron Sample Scanning Piezo
- DAQ - National Instruments PCIe-6738
- Remote Focusing System - Equipment Solutions LFA-2010 Linear Focus Actuator
- Galvo - Novanta CRS 4 KHz Resonant Galvo

.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_ctaslmv2.yaml
       :language: yaml

|


Spectral TIRF
=============

- Laser source - Omicron LightHUB Ultra. Requires ACC operating mode with analog modulation enabled for 488 nm and 642 nm lasers. 561, which operates separately, requires the mixed modulation mode (Obis).
- Camera - Hamamatsu Flash 4.0 with frame grabbers.
