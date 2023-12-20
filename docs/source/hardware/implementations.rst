==========================
Microscope Implementations
==========================

Multiscale Microscope
=====================

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Equipment
     - Description
   * - Lasers
     - Omicron LightHUB Ultra with 488, 561, and 642 nm lasers.
   * - Stages
     - PI L-509.20DG10, L-509.40DG10, L-509.20DG10, M-060.DG, M-406.4PD, PI P726.1CD
   * - Stage Controllers
     - C-884, E-709
   * - Cameras
     - Hamamatsu Flash 4.0, Hamamatsu Fusion
   * - Filter Wheel
     - Sutter Lambda 10-3 with 2x 32mm High-Speed Filter Wheels
   * - Remote Focusing Units
     - Optotune Electrotunable Lens (EL-16-40-TC-VIS-5D-1-C) and Equipment Solutions LFA-2004
   * - Data Acquisition Cards
     - National Instruments PXIe-1073 chassis equipped with PXI6733 and PXI6259
   * - Galvo
     - Novanta CRS 4 KHz Resonant Galvo and Thorlabs GVS112 Linear Galvo
   * - Zoom
     - Dynamixel MX-28R

.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_multiscale.yaml
       :language: yaml


|

Expansion ASLM
==============

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Equipment
     - Description
   * - Lasers
     - Omicron LightHUB Ultra with 405, 488, 561, and 642 nm lasers.
   * - Stages
     - ASI FTP-2000 with Linear Encoders in X and Y, and 3x LS-50 Linear Stages
   * - Stage Controllers
     - ASI Tiger Controller
   * - Cameras
     - Hamamatsu Lightning and Photometrics Iris15
   * - Filter Wheel
     - 2x ASI 6-Position 32 mm Filter Wheels
   * - Remote Focusing Units
     - ThorLabs BLINK
   * - Data Acquisition Cards
     - National Instruments PXIe-1073 chassis equipped with PXI6733 and PXI6259
   * - Galvo
     - Novanta CRS 4 KHz Resonant Galvo
   * - Zoom
     - N/A


.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_upright.yaml
       :language: yaml

|

OPM-V2
======


.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Equipment
     - Description
   * - Lasers
     - Coherent Galaxy with 488, 561, and 642 nm lasers.
   * - Stages
     - ASI FTP-2000 with MS-2000 XY stage, and a Galvo for acquisition of z-stacks.
   * - Stage Controllers
     - ASI Tiger Controller
   * - Cameras
     - Hamamatsu Flash 4.0
   * - Filter Wheel
     - 2x ASI 6-Position 32 mm Filter Wheels
   * - Remote Focusing Units
     - Optotune Electrotunable Lens (EL-16-40-TC-VIS-5D-1-C)
   * - Data Acquisition Cards
     - National Instruments PCIe-6738
   * - Galvo
     - Novanta CRS 4 KHz Resonant Galvo, and 2x Novanta Linear Galvos for shearing and tiling.
   * - Zoom
     - N/A


.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_OPMv2.yaml
       :language: yaml

|

CT-ASLM-V1
==========

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Equipment
     - Description
   * - Lasers
     - Coherent Obis lasers with emission at 488, 561, and 642 nm.
   * - Stages
     - MP-285 and Piezo Jena 200-micron piezo for acquisition of z-stacks via sample scanning.
   * - Stage Controllers
     - Sutter MP-285
   * - Cameras
     - Hamamatsu Flash 4.0
   * - Filter Wheel
     - Sutter Lambda 10-3 with 1x 25mm Filter Wheel
   * - Remote Focusing Units
     - Equipment Solutions LFA-2010 Linear Focus Actuator
   * - Data Acquisition Cards
     - National Instruments PCIe-6738
   * - Galvo
     - Novanta CRS 4 KHz Resonant Galvo
   * - Zoom
     - N/A


.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_ctaslmv1.yaml
       :language: yaml

|

CT-ASLM-V2
==========

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Equipment
     - Description
   * - Lasers
     - Coherent Obis lasers with emission at 405, 488, 561, and 642 nm.
   * - Stages
     - Sutter MP-285 and Mad City Lab 500-micron piezo for acquisition of z-stacks via sample scanning.
   * - Stage Controllers
     - Sutter MP-285
   * - Cameras
     - Hamamatsu Flash 4.0
   * - Filter Wheel
     - Sutter Lambda 10-3 with 1x 25mm Filter Wheel
   * - Remote Focusing Units
     - Equipment Solutions LFA-2010 Linear Focus Actuator
   * - Data Acquisition Cards
     - National Instruments PCIe-6738
   * - Galvo
     - Novanta CRS 4 KHz Resonant Galvo
   * - Zoom
     - N/A


.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_ctaslmv2.yaml
       :language: yaml

|


Spectral TIRF
=============

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Equipment
     - Description
   * - Lasers
     - Omicron LightHUB Ultra with 405, 457, 488, 514, 532, 561, and 642 nm lasers.
   * - Stages
     - ASI LS-50 linear stage and MS-2000 XY stage.
   * - Stage Controllers
     - ASI Tiger Controller
   * - Cameras
     - 2x Hamamatsu Flash 4.0
   * - Filter Wheel
     - 2x ASI 6-Position 32 mm Filter Wheels, and 1x motorized ASI dichroic slider.
   * - Remote Focusing Units
     - N/A
   * - Data Acquisition Cards
     - National Instruments PCIe-1073 chassis equipped with PCIe-6259 and PCIe-6738
   * - Galvo
     - 2x Novanta Linear Galvos.
   * - Zoom
     - N/A


.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_spectral_tirf.yaml
       :language: yaml


|

Live-Cell ASLM
==============

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Equipment
     - Description
   * - Lasers
     - Coherent Obis with emission at 405, 457, 488, 514, 561, and 642 nm.
   * - Stages
     - MP-285, PI P-726 PIFOC High-Load piezo, and a galvo for acquisition of z-stacks.
   * - Stage Controllers
     - Sutter MP-285 and PI E-709
   * - Cameras
     - 2x Hamamatsu Flash 4.0
   * - Filter Wheel
     - Sutter Lambda 10-3 with 1x 25mm Filter Wheels
   * - Remote Focusing Units
     - Equipment Solutions LFA-2010 Linear Focus Actuator
   * - Data Acquisition Cards
     - National Instruments PCIe-6738
   * - Galvo
     - Novanta CRS 4 KHz Resonant Galvo
   * - Zoom
     - N/A


.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_voodoo.yaml
       :language: yaml


|


BioFrontiers OPM
=================

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Equipment
     - Description
   * - Lasers
     - 3i LaserStack with 405, 488, 561, and 642 nm lasers.
   * - Stages
     - ASI FTP-2000 with MS-2000 XY stage, and a Galvo for acquisition of z-stacks.
   * - Stage Controllers
     - ASI Tiger Controller
   * - Cameras
     - Hamamatsu Flash 4.0
   * - Filter Wheel
     - ASI 8-Position 25 mm Filter Wheel
   * - Remote Focusing Units
     - N/A
   * - Data Acquisition Cards
     - National Instruments PCIe-6723
   * - Galvo
     - Thorlabs GVS112 Linear Galvo
   * - Zoom
     - N/A


.. collapse:: Configuration File

    .. literalinclude:: configurations/configuration_biofrontiers.yaml
       :language: yaml


|