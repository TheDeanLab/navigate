Camera bit depth implementation plan
====================================

For agentic workers: use superpowers:executing-plans for inline implementation;
use test-driven development and a fresh code review before publishing each PR.

Goal: expose validated camera bit depth and reduce acquisition/storage payloads.
Architecture: additive capability contracts, negotiated normalized image formats,
SDK-specific layouts, and asynchronous controller-to-model commands.
Tech stack: Python 3.9.7+, Tk, NumPy, DCAM ctypes, existing image writers.
Spec: ../specs/2026-11-05-camera-bit-depth.rst

Global constraints
------------------

Follow the spec and repository AGENTS.md. Do not change legacy defaults or enable
partial controls. Do not access physical hardware in automated non-hardware tests.
Use the existing virtual environment with PYTHONPATH pointing to this worktree.

Review focus
------------

* Unknown meaningful depth must not be reported as 16 merely because dtype is u16.
* Failed or malformed native discovery must not advertise writable settings.
* Same-size dtype changes must invalidate all old shared-memory consumers.
* File metadata and allocation estimates must use storage width, not camera bits.
* Camera mode/reconnect changes must invalidate stale capabilities and UI replies.

Task 1: Contracts and DCAM discovery (PR 1)
-------------------------------------------

Files: camera/base.py, new camera/format.py, HamamatsuAPI.py; new
 test/model/devices/camera/test_camera_format.py and DCAM boundary tests.
Interfaces: CameraSettingCapability(current_value, choices, writable,
 requires_idle, reason); CameraImageFormat(dtype, bit_depth); CameraBase
 get_advanced_setting_capabilities(), get_bit_depth(), set_bit_depth(int),
 get_image_format(); DCAM get_property_values(name), is_property_writable(name).

[ ] Write tests for legacy default unknown depth/u16, explicit unsupported setter,
    8/12/16 normalized formats, invalid format rejection and serialization.
[ ] Run focused tests and observe missing interfaces fail.
[ ] Add frozen serializable contracts and concrete CameraBase fallback methods.
[ ] Test sparse DCAM values 8/12/16, fixed/read-only properties, failed query,
    non-progressing/out-of-range/native NaN values, 64-bit handle prototypes,
    and no writes during discovery using the existing fake native library.
[ ] Add named depth/layout properties and queryvalue prototypes/helpers.
[ ] Run focused and practical broad suite, Black and git diff --check.
[ ] Record evidence, review, commit and open draft PR against develop.

Task 2: Dtype-aware acquisition and processing (PR 2)
-----------------------------------------------------

Files: model/model.py, microscope.py, controller/controller.py, camera_view.py,
 camera/synthetic.py and corresponding model/controller tests.
Consumes CameraImageFormat. Produces dtype-aware get/update_data_buffer and
 normalized synthetic uint8/uint16 frames, without exposing the popup yet.

[ ] Read controller/README.md and trace shared-memory ownership and all consumers.
[ ] Test same-shape dtype replacement, virtual cameras, consumer rebinding and
    known 8/12/16 patterns before modifying the pipeline.
[ ] Negotiate formats while idle, rebuild buffers by shape/dtype/binning and
    update temporary images, display/projections and affected arithmetic.
[ ] Run focused plus broad non-hardware tests, review and commit as PR 2.

Task 3: Native-depth storage (PR 3)
-----------------------------------

Files: data_sources/*.py, metadata_sources/*.py, features/image_writer.py and
 corresponding file round-trip tests. Consume actual normalized dtype/depth.

[ ] Add 8/12/16 round-trip tests for every writer, metadata and byte estimates.
[ ] Derive dtype from confirmed acquisition format; record significant bits
    separately; adapt readback and projection writing. Preserve compression policy.
[ ] Verify exact pixels, dtype and format interoperability, review and PR 3.

Task 4: Hamamatsu control (PR 4)
--------------------------------

Files: camera/hamamatsu.py, APIs/hamamatsu/HamamatsuAPI.py, microscope.py and tests.
Consumes contracts and complete dtype pipeline. Produces supported depth setter
 and verified native frame layout; Lightning remains read-only pending mapping.

[ ] Test exact readback, rejected values, partial-change rollback, acquiring
    camera refusal, buffer layout validation and Quest restart preservation.
[ ] Implement bounded capability intersection, transaction, layout conversion,
    and timing refresh before buffer attachment. Missing saved field is no-op.
[ ] Verify native fake boundaries and integration tests, review and PR 4.

Task 5: UI and persistence (PR 5)
---------------------------------

Files: camera_setting_popup.py, sub_controllers/camera_settings.py,
 controller/controller.py, model/model.py, model/microscope.py, config/config.py.
Consumes capabilities and setter; produces identity-tagged asynchronous results.

[ ] Test disabled states, same-camera acquisition locking, stale responses,
    save/switch/close while pending, config round trips and failed application.
[ ] Add widget and commands with Tk/main-thread event updates and confirmed saves.
[ ] Test synthetic end-to-end acquisition/save/reopen, review and PR 5.

Follow-ups
----------

Write focused plans before each vendor or compression PR using the same contracts.
Lightning owns coupled full-well timing/calibration semantics. Ximea owns SDK image
format dependencies; Daheng owns supported monochrome PixelFormats; Photometrics
reports coupled readout depth without inventing an independent setter. Compression
PRs independently validate TIFF, Zarr and H5/N5 interoperability and performance.
