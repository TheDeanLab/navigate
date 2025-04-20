======
Lasers
======
We currently support laser control via voltage signals. In the near-future, we will consider implementing
laser control via serial communication for power control, but digital modulation will still be controlled via
voltage signals.

---------------------

Analog/Digital-Controlled Lasers
--------------------------------

Most lasers are controlled externally via mixed analog and digital modulation.
The ``onoff`` entry is for digital modulation. The ``power`` entry is for analog
modulation.

.. note::
    Omicron LightHUB Ultra laser launches include both Coherent- and LuxX lasers,
    which vary according to wavelength. LuxX lasers should be operated in an ACC
    operating mode with the analog modulation option enabled. The Coherent Obis lasers
    should be set in the mixed modulation mode.

.. note::
    Coherent Obis lasers should be set in the mixed modulation mode. It is not uncommon
    for the slew rate from the data acquisition card to be insufficient to drive the modulation
    of the laser if the laser is set to an analog modulation mode.

.. note::
    Users have reported intermittent connection issues at random intervals arising
    from USB-based communication instance with Coherent Obis controllers. Specifically,
    these errors were observed as a conflict over COM port assignments between the
    Coherent OBIS laser and the ASI Tiger controller. These issues are discussed in
    depth in the :ref:`communication challenges <obis_tiger_connection>` section.


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            lasers:
               -
                wavelength: 488
                onoff:
                  hardware:
                    type: NI
                    channel: PXI6733/port0/line2
                    min: 0.0
                    max: 5.0
                power:
                  hardware:
                    type: NI
                    channel: PXI6733/ao0
                    min: 0.0
                    max: 5.0
               -
                wavelength: 561
                onoff:
                  hardware:
                    type: NI
                    channel: PXI6733/port0/line3
                    min: 0.0
                    max: 5.0
                power:
                  hardware:
                    type: NI
                    channel: PXI6733/ao1
                    min: 0.0
                    max: 5.0

|

-------------------


Synthetic Lasers
--------------------------------


.. collapse:: Configuration File

    .. code-block:: yaml

      microscopes:
        microscope_name:
            lasers:
               -
                wavelength: 488
                onoff:
                  hardware:
                    type: synthetic
                    channel: PXI6733/port0/line2
                    min: 0.0
                    max: 5.0
                power:
                  hardware:
                    type: synthetic
                    channel: PXI6733/ao0
                    min: 0.0
                    max: 5.0
               -
                wavelength: 561
                onoff:
                  hardware:
                    type: synthetic
                    channel: PXI6733/port0/line3
                    min: 0.0
                    max: 5.0
                power:
                  hardware:
                    type: synthetic
                    channel: PXI6733/ao1
                    min: 0.0
                    max: 5.0

|
