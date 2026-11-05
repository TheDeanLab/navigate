.. _camera_capabilities:

Camera capabilities and image formats
=====================================

Camera adapters describe advanced settings through
:code:`get_advanced_setting_capabilities()`. Each entry contains a
:code:`CameraSettingCapability` with the current value, available choices,
whether the adapter can change the value, whether acquisition must be stopped,
and an explanation when the control is unavailable.

Query the connected device instead of inferring its capabilities from its model
name. The connection type, driver version and operating mode can affect which
settings are available. Querying capabilities must not change camera settings.
Discard incomplete results after a driver error; a partial list is not a
reliable description of the connected camera.

The base implementation reports bit-depth control as unavailable and
:code:`set_bit_depth()` raises :code:`NotImplementedError`. The methods are
concrete, so existing adapters continue to load without implementing them.
An adapter can report a readable current value while leaving selection disabled.
Only advertise writable choices when the complete acquisition path supports them.

Keep three representations distinct
-----------------------------------

* **Camera output depth** describes meaningful output precision. It can be
  unknown even when the array storage type is known.
* **SDK transport layout** describes incoming bytes, including packed pixels,
  row padding and bit alignment. The camera adapter owns this layout.
* **Array format** describes the unpacked, right-aligned monochrome values that
  the adapter delivers to **navigate**. :code:`CameraImageFormat` records the
  NumPy dtype and optional meaningful bit depth.

For example, :code:`CameraImageFormat.for_bit_depth(8)` selects
:code:`uint8`, while :code:`CameraImageFormat.for_bit_depth(12)` selects
:code:`uint16` with 12 meaningful bits. The latter still uses two bytes per
pixel. Never reinterpret packed native bytes as an unpacked array, and never
infer camera precision from the brightest pixel in a frame.

Legacy adapters return :code:`CameraImageFormat()` with a :code:`uint16` array
and unknown meaningful depth. This preserves the existing buffer contract
without making a claim about the sensor's precision.

DCAM discovery
--------------

The Hamamatsu wrapper exposes :code:`get_property_values(name)` for small
discrete settings and :code:`is_property_writable(name)` for the SDK writable
attribute. Enumeration uses :code:`dcamprop_queryvalue` rather than filling the
interval between the minimum and maximum. Missing properties, malformed values,
non-progressing enumeration and failed queries return an unavailable result.

The writable attribute alone does not authorize a setting change during
acquisition. Adapters must enforce idle requirements and verify actual readback
when implementing setters. A successful SDK query is not evidence of physical
acquisition validation for a particular model and interface.

Hamamatsu validation boundaries
-------------------------------

DCAM depth choices are discovered from the connected camera in its current mode.
The adapter checks exact readback and restores captured settings if application
fails. A failed restoration blocks acquisition until the camera is reconnected.
Quest restart restores and verifies depth and pixel type before attaching buffers.

Only unpacked MONO8 and MONO16 layouts are currently accepted. Row padding and
buffer top offsets are handled using native scratch buffers; normalized arrays
preserve integer counts without scaling. Packed MONO12/MONO12P and color layouts
are rejected. An advertised 12-bit option therefore still requires a supported
unpacked transport layout. ORCA-Lightning remains read-only until its coupled
High Dynamic Range/full-well mode and timing changes are implemented.

Automated fake-SDK tests cover discovery, rollback, attachment, padding, offsets,
range checks and restart failures. They do not certify a physical camera model.
Before declaring a model tested, record its model/serial, firmware, DCAM version,
connection, sensor/readout mode, each offered depth, confirmed native layout,
exact saved counts and measured acquisition throughput. Repeat after a restart
and a mode change. Unsupported or untested models must never receive guessed
choices from a product-name table.
