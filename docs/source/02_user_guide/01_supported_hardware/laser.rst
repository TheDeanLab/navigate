.. _laser_configuration:

======
Lasers
======

**navigate** supports laser control through external electrical signals and optional
software connections to the laser. In the configuration file, ``onoff`` selects the
electrical gate and ``power`` normally selects analog modulation. Existing
configurations continue to work without adding any settings.

.. _advanced_laser_settings:

Advanced laser settings
-----------------------

Open :menuselection:`Microscope Configuration --> Advanced Laser Settings` and
select a microscope and laser. Lasers with a ``software_control`` adapter show
their connection status, supported modulation modes, internal power limits,
percentage reference, internal setpoint, emission status, and reported output
power. A laser without this optional configuration shows
:guilabel:`Software control not configured`; existing NI/ASI operation is unchanged.

Use :guilabel:`Refresh` for a new reading. Unknown or unavailable readings are
shown explicitly, and synthetic adapters are labeled simulated. The internal
setpoint is the peak pulse setting in digital mode and the CW setting in CW mode.
Analog and mixed modes use external voltage for amplitude, so the popup does not
present an internal setting as their output power. Reported output power comes
from the laser and is not a sample-plane measurement.

Select a mode and click :guilabel:`Apply mode`. CW, digital, analog, and mixed
modes are available when supported by the adapter and compatible with the power
source. Serial channel power requires CW or digital mode; OBIS requires digital
mode unless explicit bench mode is enabled. The selected mode must match the
installed electrical wiring. Mode changes command the shutter and electrical
gates closed and leave them closed until acquisition prepares illumination.
Emission is never enabled by this popup.

Software settings changes stop if an NI output write or ASI command acknowledgement
fails during blanking. An acknowledgement confirms receipt of the command; it does
not measure shutter position or optical extinction. Confirm the installed wiring
and shutter timing before acquisition.

A confirmed mode applies for the current session, including subsequent
acquisitions. :guilabel:`Next acquisition mode` shows this selection or the startup
policy. The popup does not rewrite configuration or experiment files; set
``software_control.mode`` in the configuration to change the startup policy.
Channel power continues to be set in :guilabel:`Power (%)` in the Channels tab.
After a mode change, channel confirmations become pending until acquisition
reapplies and verifies power.

Acquisition metadata includes the confirmed mode for software-controlled lasers,
including lasers whose power still comes from an external analog signal. Their
external power remains marked unverified.

Settings requests run outside the GUI thread. Read and write requests are
disabled during acquisition. Start acquisition after any in-flight request has
finished. A failed mode change must be corrected and confirmed before acquiring;
a failed serial connection requires restarting **navigate**.

Optional serial power control
-----------------------------

Use serial power control when the laser should receive its power setting from
**navigate**, while an NI or ASI output continues to control illumination timing.
Supported software adapters are Vortran Stradus, Coherent OBIS LX/LS, and
the original Omicron LuxX, through their serial interfaces.
The laser must already be powered, enabled, and ready to accept commands, as with
electrical control. The adapter does not enable emission or change emission delays.
It uses the existing ``pyserial`` dependency; an additional vendor Python package
is not required. Native USB HID connections are not supported.

1. Keep the existing ``onoff`` configuration for the digital gate.
2. Set ``power.source`` to ``serial`` and ``power.hardware.type`` to ``Synthetic``.
   In this position, ``Synthetic`` means that no analog power output is allocated.
3. Add ``software_control`` with the adapter type and RS232 port.
4. Choose a supported operating mode, or omit ``mode`` to preserve the current
   laser mode. Serial amplitude control requires CW or digital mode; analog and
   mixed modes use the external analog voltage for amplitude.
5. Optionally set ``power.percent_reference_mw`` to define the power represented by
   100 percent. If omitted, the adapter queries the laser's maximum power.

For example, this laser uses NI digital gating and Vortran serial power:

.. code-block:: yaml

    laser:
      - wavelength: 488
        onoff:
          hardware:
            type: NI
            channel: Dev1/port0/line0
            min: 0.0
            max: 5.0
        power:
          source: serial
          percent_reference_mw: 100.0
          hardware:
            type: Synthetic
        software_control:
          type: Vortran
          port: COM7
          baudrate: 19200
          timeout: 2.0
          mode: digital

Place this entry under the appropriate microscope in :file:`configuration.yaml`.
For ASI gating, retain the existing ASI ``onoff`` block instead. Setting
``software_control.type`` to ``Synthetic`` provides an in-memory settings adapter
for testing; its optional ``max_power_mw`` defaults to 100. Virtual Devices mode
also substitutes this adapter for a configured Vortran connection.

Each real laser serial port must have one ``software_control`` owner across all
microscopes. Preload rejects duplicate port assignments, including Windows COM
case differences and Linux device symlinks. Sharing a software-controlled laser
between microscope definitions is not supported yet.

The channel :guilabel:`Power (%)` field keeps its existing percentage meaning.
With the example above, 25 percent requests 25 mW. No new fields are required in
:file:`experiment.yml`. During acquisition or live imaging, a label below the
power field shows the confirmed internal setting in mW. Changing the field marks
the request pending until channel preparation applies it. The software closes the
shutter during a serial power change and reopens it after success. Electrical
gating retains the existing acquisition timing. Serial updates add channel-switching
latency; unchanged settings are cached until the next acquisition preparation.

Vortran distinguishes its laser-enable input from its optional digital modulation
input. CW requires gating through the laser-enable input; it cannot be gated by
an inactive digital modulation input. Digital mode requires the corresponding
digital modulation wiring. Firmware may require
emission to be enabled before accepting a power change. Rejected commands, missing
responses, and mismatched readbacks stop acquisition. Protocol-emulator tests do
not establish physical device behavior; confirm the mode, gating, power readback,
and settling time on the installed laser before collecting experimental data.
After a serial communication failure, restart **navigate** to establish a new
connection before acquiring again.

.. _vortran_digital_modulation_wiring:

Vortran digital modulation wiring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For camera-driven digital modulation, connect the camera timing output to the
digital-modulation SMB connector on the rear of the Stradus laser head. The
analog input on the front of the control box serves analog power control;
selecting digital mode in **navigate** does not turn that connector into a
digital-modulation input. See sections 6.3.10 and 8.6 of the
`Vortran Stradus user manual <https://preview-assets-us-01.kc-usercontent.com/078db625-9c43-005d-663d-c89ba2b8888d/eaba4f91-42f3-405f-abb3-8b61f863e873/Stradus%20Manual.pdf>`_.

In a user-reported bench check on November 25, 2026, camera output voltage pulses
were visible on an oscilloscope, but the laser did not respond in digital mode
when connected to the control box's front analog input. Moving the signal to the
rear SMB connector on the laser head produced the expected laser response.
This confirms the connector choice on that setup; it does not establish optical
pulse timing, calibrated power, or compatibility with every camera and laser model.

If camera pulses are present but the laser does not respond, check the physical
connector as well as the mode readback. Verify signal levels and termination
against the manuals for the installed camera and laser; a voltage measured with
an unloaded oscilloscope input may differ from the voltage at the connected laser.

.. _laser_serial_bench:

Serial-only bench testing
~~~~~~~~~~~~~~~~~~~~~~~~~

For a laser without an NI/ASI gate, explicitly set
``software_control.bench_mode: true``, ``power.source: serial``, and both
``onoff.hardware.type`` and ``power.hardware.type`` to ``Synthetic``. The adapter
still connects to the real laser. For example:

.. code-block:: yaml

    laser:
      - wavelength: 488
        onoff:
          hardware:
            type: Synthetic
        power:
          source: serial
          percent_reference_mw: 10.0
          hardware:
            type: Synthetic
        software_control:
          type: Vortran
          port: COM7
          bench_mode: true
          mode: preserve

Replace the port with the installed adapter's port. On Linux, a persistent
:file:`/dev/serial/by-id/` path avoids USB numbering changes. Start **navigate**
normally: Virtual Devices mode (``-sh``) substitutes a simulated laser adapter.
Use :guilabel:`Advanced Laser Settings` to inspect the connection and select a
compatible mode. Channel :guilabel:`Power (%)` applies during live imaging or
acquisition; in this example, 100 percent requests 10 mW.

The popup labels this configuration :guilabel:`Serial (bench; no gating)`.
**navigate** does not gate illumination in this setup, including when acquisition
stops. The laser's emission state remains under the user's control. Bench mode is
intended for enclosed bench testing, not exposure-synchronized microscopy, and
defaults to false when omitted. Confirmed metadata includes ``bench_mode: true``.

Vortran timing and power resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Omit ``timeout`` to use the Vortran default of 2 seconds. Stradus configuration
and power writes can take about one second even when queries respond quickly;
a 0.5-second timeout can fail during connection. Explicit timeout values are
honored. Other software adapters retain their 0.5-second default.

CW settings are rounded to tenths of a milliwatt. Digital peak-power settings
are rounded to whole milliwatts before writing, matching the pulse-power
register on Stradus firmware 3.2.0. The confirmed value records this rounding.
CW and digital power control both require constant-power control (``C=0``);
explicit mode selection configures this before applying modulation settings.
Preserving an existing constant-current setting does not make it compatible
with serial power control.

On the tested firmware, a zero CW power command is rejected, and enabling
digital modulation while emission is disabled is also rejected. **navigate**
reports these failures without claiming a successful setting or enabling
emission automatically. Use the electrical gate for illumination timing.

Serial communication, readbacks, all four modulation modes with emission
enabled, and low-power setpoints were exercised on a 488 nm, 250 mW Stradus
with firmware 3.2.0 / protocol 1.0.5 through a USB-to-RS232 adapter. These checks
do not validate NI/ASI electrical timing, optical calibration, or other
firmware versions. Allow for serial channel-switching latency; verified power
updates on this unit took approximately 1.2--1.4 seconds.

OBIS and LuxX software control
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The same ``software_control`` block selects the additional adapters. Omit
``baudrate`` to use the adapter-specific default, or specify it to match the
device. The existing Vortran default remains 19200 baud.

.. list-table:: Serial software adapters
   :header-rows: 1
   :widths: 20 20 35 25

   * - ``type``
     - Default baud rate
     - Software modulation choices
     - Serial channel power
   * - ``OBIS``
     - 115200
     - CW, digital, analog, mixed
     - Digital; CW (CWP) in bench mode only
   * - ``LuxX``
     - 500000
     - CW, analog
     - CW

For an OBIS laser with serial channel power, retain the NI/ASI gate and the
``power`` block from the configuration example and replace ``software_control``:

.. code-block:: yaml

    software_control:
      type: OBIS
      port: COM4
      mode: digital

For an original LuxX, use:

.. code-block:: yaml

    software_control:
      type: LuxX
      port: COM19
      mode: cw

Omitting ``mode`` preserves the device's current setting. Selecting CW applies
CWP on OBIS and CW-APC on LuxX. OBIS constant-current mode (CWC) is preserved when
requested, but serial power requires selecting digital first (or CWP for bench
testing). OBIS CW disables external modulation; an NI/ASI output connected to its
modulation input cannot gate CW illumination. Normal serial acquisition therefore
rejects OBIS CW, including when ``mode: preserve`` reads an existing CW setting.

The original LuxX has CW and analog operating modes, with a separate electrical
laser-enable input. NI/ASI continues to drive that input for acquisition timing;
there is no digital or mixed software mode to select on this model. LuxX+ and
other Omicron models are not covered by this adapter. The popup advertises only
supported modes, including in Virtual Devices mode. A LuxX in standby remains
connected in the popup and can be switched to CW or analog; acquisition with
``mode: preserve`` stops until a usable mode is selected.

OBIS protocol values are in watts and are converted to mW by the adapter. LuxX
power is quantized to its 12-bit register; the confirmed mW value reflects that
quantization rather than repeating the requested value. Both adapters read the
internal setpoint and measured output separately. Neither connection nor power
updates enable emission, set autostart, or call the API's legacy initialization
routine. Their connections use finite read/write timeouts and complete response
frames, so communication failures cannot silently reuse a previous reply.

The popup does not save its mode override to **navigate** configuration files.
Device firmware can retain changes independently: OBIS saves mode and power
settings in persistent memory. Re-preparing a microscope within one acquisition
verifies the mode without repeating explicit mode writes. Consult the
`Coherent OBIS operator's manual <https://www.coherent.com/resources/manuals/lasers/obis-lx-ls-operators-manual.pdf>`_
and the
`Omicron-authored Micro-Manager driver <https://github.com/micro-manager/mmCoreAndDevices/blob/main/DeviceAdapters/Omicron/Omicron.cpp>`_
for protocol and mode details. Protocol-emulator tests do not establish physical
hardware behavior; verify power, mode, and electrical gating on the installed
laser.

The OBIS adapter currently requires the setpoint readback to agree within
0.001 mW. Its serial register resolution still needs physical validation,
including fractional requests such as 18.315 mW; vendor GUI step sizes alone
do not establish serial quantization. A mismatch raises an error rather than
recording the requested setting as confirmed.

Laser power metadata
~~~~~~~~~~~~~~~~~~~~

:file:`experiment.yml` retains the requested channel percentage. Each image output
directory additionally receives :file:`laser-settings-<microscope>.jsonl`, for TIFF,
OME-TIFF, H5, N5, and OME-Zarr alike. Each line is a JSON record of a requested,
prepared, or failed channel setting. Records include the channel, acquisition
identifier, sequence, timestamp, power source, requested percentage, and, when
available, its mW reference and confirmed internal setting. Changes append records
instead of replacing earlier settings. Repeated identical channel settings are
not recorded for every image. History survives microscope re-preparation and
resolution changes within an acquisition. Starting a new acquisition creates a
new history. Closing a saved output prevents later live-session records from
being appended to that experiment's sidecar.

The records describe channel preparation, not per-image optical measurements.
``confirmed_setpoint_mw`` is the internal setting or calibrated peak pulse readback.
``measured_power_mw``, when available, is a separate laser-reported reading obtained
after configured blanking commands during preparation (ungated in bench mode);
it is not sample-plane power or an
exposure-average measurement. Missing values are stored as ``null``. Synthetic
confirmations are marked ``simulated``. Existing electrical-only control is marked
``unverified_external`` rather than being presented as measured optical power.

Only one application should control a laser's settings during an acquisition.
Cached confirmations assume that another application does not change them.

Leaving out ``software_control`` (or selecting ``type: None``) and leaving out
``power.source`` preserves electrical-only behavior. The defaults do not open a
serial connection, change the laser mode, or reinterpret saved channel percentages.

---------------------

Applied Scientific Instrumentation
----------------------------------

The Tiger Controller (`TG-1000 <https://asiimaging.com/docs/products/tiger>`_) from ASI can also be used to perform analog, digital, and mixed modulation of lasers. 
Digital modulation is controlled with a `TGPLC <https://asiimaging.com/docs/tiger_programmable_logic_card>`_ 
or `TGGALVO <https://asiimaging.com/docs/tggalvo>`_ control cards, while analog modulation is controlled with a TGGALVO control card.
TGPLC output 1 is reserved for the camera trigger.

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
                    type: ASI
                    axis: 2
                    min: 0.0
                    max: 5.0
                power:
                  hardware:
                    type: ASI
                    axis: A
                    min: 0.0
                    max: 5.0
               -
                wavelength: 561
                onoff:
                  hardware:
                    type: ASI
                    axis: 3
                    min: 0.0
                    max: 5.0
                power:
                  hardware:
                    type: ASI
                    axis: B
                    min: 0.0
                    max: 5.0


-------------------


National Instruments
--------------------

Most lasers are controlled externally via mixed analog and digital modulation. Thus, a NI data acquisition card may be used to control the laser. In general, an analog output can be used to control both the digital and analog modulation of the laser, whereas a digital output can only be used to control the digital modulation of the laser.

.. note::
    Omicron LightHUB Ultra laser launches include both Coherent- and LuxX lasers, which vary according to wavelength. LuxX lasers should be operated in an ACC operating mode with the analog modulation option enabled. The Coherent Obis lasers should be set in the mixed modulation mode.

.. note::
    Coherent Obis lasers should be set in the mixed modulation mode. It is not uncommon for the slew rate from the data acquisition card to be insufficient to drive the modulation of the laser if the laser is set to an analog modulation mode.

.. note::
    Users have reported intermittent connection issues at random intervals arising from USB-based communication instance with Coherent Obis controllers. Specifically, these errors were observed as a conflict over COM port assignments between the Coherent OBIS laser and the ASI Tiger controller. These issues are discussed in depth in the :ref:`communication challenges <obis_tiger_connection>` section.


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
