=============
Galvanometers
=============

Galvo mirrors are used for fast scanning, shadow reduction, and occasionally as stages
(see :ref:`Analog-Controlled Galvo/Piezo <galvo_stage>`).

------------

National Instruments
--------------------

Multiple types of galvanometers have been used, including Cambridge Technologies/Novanta, Thorlabs, and ScannerMAX. Each of these devices are externally controlled via analog signals delivered from an NI-based data acquisition card.

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

------------

ASI
---

Multiple types of galvanometers have been used, including Cambridge
Technologies/Novanta, Thorlabs, and ScannerMAX. Each of these devices
are externally controlled via analog signals delivered from the ASI 
Tiger Controller.

The ASI Tiger Controller has a few limitations for the analog signals. First, the 
minimum voltage must be zero volts. Second, the period value needs to be a whole number.
Third, there are three analog waveforms offered, sawtooth,  
triangle, and sine waves.

The sawtooth waveform is a periodic analog waveform. There are three duty cycle values 
accepted, 0, 50, and 100. If the duty cycle is 0, the waveform is a falling sawtooth 
waveform. If the duty cycle is 50, then it is a triangle wave. If the duty cycle is 100, 
the waveform is a rising sawtooth waveform. 


.. collapse:: Configuration File

    .. code-block:: yaml

        microscopes:
          microscope_name:
            galvo:
               -
                hardware:
                  type: ASI
                  axis: A
                  min: 0
                  max: 1.0
                waveform: sine
                phase: 0
               -
                hardware:
                  type: ASI
                  axis: B
                  min: 0
                  max: 1.0
                waveform: sine
                phase: 1.57079632679

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
