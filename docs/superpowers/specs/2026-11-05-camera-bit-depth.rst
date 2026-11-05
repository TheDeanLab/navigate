Camera bit depth: approved design
=================================

Intent
------

Provide operating/output bit-depth control in Advanced Camera Settings across
camera drivers, improving transfer throughput and enabling smaller saved files.
The UI reflects live capabilities and explains unavailable controls. Hardware
capability is distinct from physical validation of a particular camera.

Architecture and constraints
----------------------------

* Add concrete CameraBase capability, get/set depth and image-format interfaces;
  existing and third-party subclasses must continue to instantiate unchanged.
* Discover SDK-supported values; do not infer them from camera names or numeric
  min/max ranges. Retain explicit adapter mappings for coupled operating modes.
* Separate meaningful camera bits, SDK transport layout, shared-memory dtype and
  stored dtype. Default legacy drivers to their existing uint16 buffer contract
  without claiming their sensor has 16 meaningful bits.
* Produce uint8 for 8-bit operation and uint16 for 9-16-bit operation. Convert SDK
  layouts explicitly, preserving values. Packed 12-bit files are a later feature.
* Use type hints compatible with the project's Python floor (3.9.7), existing
  dependencies, NumPy-style docstrings and Black formatting.
* Keep SDK I/O off the Tk main thread. Keep widget and Tk-variable access on it.
* Apply changes only while idle. Verify readback, roll back rejected changes and
  prevent acquisition if restoration or layout validation fails.
* Revalidate after mode changes and preserve settings across Quest 2 restart.
* Persist selected depth per microscope in experiment CameraParameters. Missing
  fields preserve legacy behavior. Record the actual acquisition format in file
  metadata and size estimates. Never change dtype within an existing stack.
* Return capability responses with camera identity; reject stale UI responses.
* Unsupported or unimplemented setters remain disabled. Synthetic tests are not
  evidence of physical camera behavior.

Approaches considered
---------------------

A static per-model depth list is easy but stale and interface-dependent. SDK-only
control handles new models but misses coupled modes. The approved approach uses
SDK discovery with driver-specific mappings, safe fallbacks, and validated image
layouts. Lightning maps 12/16-bit operation to Standard/High full-well mode via
DCAM HighDynamicRange Mode and requires timing/calibration handling.

Delivery sequence
-----------------

1. Capability and image-format contracts plus read-only DCAM discovery.
2. Dtype-aware acquisition, buffer lifetime, processing and synthetic tests.
3. Native-depth saving/readback/metadata for all existing file formats.
4. Hamamatsu setter, layouts, timing, failure recovery and restart preservation.
5. Advanced-settings UI, asynchronous application and persistence.
6. Independent Lightning, Ximea, Daheng and Photometrics follow-up changes.
7. Independent TIFF/OME-TIFF, OME-Zarr and H5/N5 lossless compression changes.

Keep selection unavailable until its complete acquisition/storage path works.
Merge each PR separately; do not merge or alter the user's develop checkout.
Compression tuning must measure sustained fps, dropped frames, CPU, write rate
and file size; lower camera precision and lossless compression are different.

Validation
----------

Tests cover unavailable/fixed/read-only/sparse capabilities, malformed SDK
results, exact setter readback, rollback, pending acquisition, camera switching,
shared-memory rebinding, image patterns, file round trips and Quest restart.
Hardware verification is recorded separately for model/interface/mode/depth.
