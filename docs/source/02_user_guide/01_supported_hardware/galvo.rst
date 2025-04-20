=============
Galvanometers
=============

Galvo mirrors are used for fast scanning, shadow reduction, and occasionally as stages
(see :ref:`Analog-Controlled Galvo/Piezo <galvo_stage>`).

------------

Analog-Controlled Galvo
-----------------------

Multiple types of galvanometers have been used, including Cambridge
Technologies/Novanta, Thorlabs, and ScannerMAX. Each of these devices
are externally controlled via analog signals delivered from a data
acquisition card.

.. collapse:: Configuration File

    .. code-block:: yaml

        microscopes:
          microscope_name:
            galvo:
               -
                hardware:
                  type: NI
                  channel: PXI6259/ao1
                  min: -1.0
                  max: 1.0
                waveform: sawtooth
                phase: 0
               -
                hardware:
                  type: NI
                  channel: PXI6259/ao1
                  min: -1.0
                  max: 1.0
                waveform: square
                phase: 0

|

-----------------

Synthetic Galvo
---------------
If no galvo is present, one must configure the software to use a synthetic
galvo.

.. collapse:: Configuration File

    .. code-block:: yaml

        microscopes:
          microscope_name:
            galvo:
               -
                hardware:
                  type: synthetic
                  channel: PXI6259/ao1
                  min: -1.0
                  max: 1.0
                waveform: sawtooth
                phase: 0
               -
                hardware:
                  type: synthetic
                  channel: PXI6259/ao1
                  min: -1.0
                  max: 1.0
                waveform: square
                phase: 0

|
