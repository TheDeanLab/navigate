.. _camera_capabilities:

Camera capabilities and image formats
=====================================

Camera adapters describe advanced settings through
:code:`get_advanced_setting_capabilities()`. Each entry contains a
:code:`CameraSettingCapability` with the current value, available choices,
whether the adapter can change the value, whether acquisition must be stopped,
and an explanation when the control is unavailable. Optional :code:`value_labels`
contains serializable :code:`(value, label)` pairs; adapters that omit it retain
numeric labels.

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

Pixel type must be selected before precision. For example, an ORCA-Quest 2 can
report writable 12/16 choices in MONO16, then report fixed/read-only 8 after
selecting MONO8. The adapter combines the advertised pixel types with precision
choices. When idle in MONO8, it temporarily selects MONO16 to query its choices,
then restores and verifies the original format and timing before returning.
Discovery during capture, after failed restoration, or for ORCA-Lightning never
performs that probe. No camera-model table supplies guessed depth choices.

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

On 2026-11-05, direct SDK tests on a USB-connected ORCA-Quest 2 C15550-22UP,
firmware 3.20, driver 1.2.6.0 and Linux DCAM 4.0.7087 verified MONO8 capture in
Normal and Light-Sheet modes. Starting in either 12 or 16 bits, writing
BITSPERCHANNEL=8 first returned INVALIDVALUE; selecting MONO8 first succeeded
and made precision read back as 8. Native 512 by 512 frames used 262,144 bytes
in MONO8 versus 524,288 bytes in MONO16. This establishes native byte counts,
not sustained throughput or support for other camera/firmware combinations.


Scan speed and correction controls
----------------------------------

In :guilabel:`Advanced Camera Settings`, stop acquisition before changing
:guilabel:`Scan speed`, :guilabel:`Defect correction`, or
:guilabel:`Hot-pixel correction`. Each list contains choices reported by the
connected camera. Fixed, unsupported and unknown settings remain disabled.
An unavailable text label appears as its numeric SDK value; **navigate** does
not guess its meaning or infer correction strength from numeric order.

If the sensor mode selected in the main Camera Settings tab differs from the
camera's actual mode, click :guilabel:`Apply sensor mode` in the advanced popup.
This explicit idle action changes only the camera and refreshes its available
choices, ROI limits, exposure limits and readout timing. It does not start an
acquisition. Ordinary refresh remains read-only for these settings. The existing
MONO8 precision-discovery probe described above is unchanged.

The Hamamatsu adapter maps :code:`scan_speed` to DCAM :code:`READOUTSPEED`
(:code:`0x00400110`), :code:`defect_correction` to :code:`DEFECTCORRECT_MODE`
(:code:`0x00470010`), and :code:`hot_pixel_correction` to
:code:`HOTPIXELCORRECT_LEVEL` (:code:`0x00470030`). The wrapper reads value labels
with :code:`dcamprop_getvaluetext`. Only complete device enumeration supplies
choices: global SDK enum definitions do not establish camera support. In
particular, scan labels and supported speeds can differ between Quest 2 and
Fusion BT. Photon-number-resolving sensor mode is not exposed by this feature.

Adapters implement :code:`get_advanced_setting(name)` and
:code:`set_advanced_setting(name, value)`. The base class leaves the new settings
unavailable. The synthetic camera provides simulated controls, including a
fixed Standard scan speed in Light-Sheet mode, for testing without hardware.
It does not simulate the physical noise-reduction effects of correction.

Transactions and persistence
---------------------------

New model requests include :code:`setting` and :code:`value`, alongside the
existing microscope, connection identity and request ID. Replies include
:code:`capabilities` for all settings and confirmed timing after a named change.
Legacy :code:`bit_depth` requests and the singular :code:`capability` reply remain
supported. SDK work runs on the serialized model worker; the controller applies
widget updates on the Tk main thread and discards stale replies.

The camera snapshots mode, format, ROI, correction and timing dependencies
before a named change. It verifies readback and the resulting image layout,
refreshes dependent choices, and restores the snapshot if the write or buffer
negotiation fails. :code:`snapshot_advanced_settings()` and
:code:`restore_advanced_settings(snapshot)` allow model failures to use the same
rollback. Failed restoration blocks writes and acquisition for all microscope
aliases sharing the physical connection until it is reconnected. SDK failure
sentinels are never accepted as numeric zero or an Off value.

Confirmed selections are saved per microscope under the experiment's
:code:`CameraParameters` keys :code:`scan_speed`, :code:`defect_correction`, and
:code:`hot_pixel_correction`. Save the experiment to retain them across sessions.
Preparation applies sensor mode, saved scan speed, ROI/binning, saved bit depth,
and saved correction values before allocating image buffers. Missing keys in
older experiments do not create new correction selections. A saved scan speed
prevents the Hamamatsu constructor's legacy fastest-speed initialization.
Invalid or unavailable saved selections stop preparation rather than silently
substituting an unsupported value.

Acquisition preparation captures actual settings independently of pending UI
values. TIFF stores them in :code:`camera_settings`, OME-TIFF uses a referenced
map annotation, and H5, N5 and OME-Zarr store :code:`camera_scan_speed`,
:code:`camera_defect_correction` and :code:`camera_hot_pixel_correction` attributes.
Unknown values are omitted. These controls do not rescale pixels or change the
native normalized dtype except when a confirmed camera format change requires
new buffers. The optional Quest 2 restart also restores hot-pixel correction
when the SDK reports it.

Automated tests cover fake SDK transactions, real Tk popup controls, experiment
save/reload, and native pixel/metadata round trips through every supported image
writer. These tests do not validate correction effects or scan performance on
physical hardware; no new hardware acquisition is claimed by this feature.
