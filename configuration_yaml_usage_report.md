# `configuration.yaml` Usage Audit

Audit target: `src/navigate/config/configuration.yaml`

Date: 2026-06-14

## Method

I treated this as a runtime/config-loader audit, not a documentation grep.

- Parsed the YAML into 303 scalar entries and 98 container entries.
- Normalized duplicated microscope/list paths into 101 distinct leaf-schema paths, for example `microscopes.<microscope>.stage.hardware.[].axes.[]`.
- Collapsed repeated filter labels, zoom labels, solvents, and axes into placeholder path segments while preserving the raw scalar-entry counts.
- Traced direct runtime access through `load_configs()`, `verify_configuration()`, `verify_experiment_config()`, `verify_waveform_constants()`, `Microscope`, `ConfigurationController`, device startup, concrete device classes, metadata writers, and relevant controllers.
- Counted tests, docs, and `configuration_database.py` as supporting evidence for schema/UI exposure, but not as proof of runtime usage.

Status definitions:

- **Used**: read by the default runtime path or by a concrete built-in code path that the packaged default can activate after normal verification.
- **Possibly used**: supported by repo code for alternate hardware/device types or configurator schema, but not used by the packaged default hardware path as written.
- **Not used**: no runtime consumer for the packaged entry in this repo. Some of these are still mentioned in tests/docs/configurator metadata and would need corresponding cleanup.

## Executive Summary

The file is mostly active hardware/schema data, but there are clear cleanup candidates.

- **Not used as packaged:** 14 normalized leaf-schema paths, covering 22 scalar YAML entries.
- **Possibly used / alternate hardware only:** 14 normalized leaf-schema paths, covering 38 scalar YAML entries.
- **Used:** 73 normalized leaf-schema paths, covering 243 scalar YAML entries.

High-confidence cleanup candidates:

- `BDVParameters.*`: top-level entries in `configuration.yaml` are not consumed. BDV code reads `configuration["experiment"]["BDVParameters"]`.
- `gui.channels.count`: overwritten by `verify_configuration()` before `verify_experiment_config()` reads it.
- `microscopes.<microscope>.camera.settle_down`: no runtime consumer; runtime code looks for `settle_duration` or waveform `camera_settle_duration`.
- `microscopes.<microscope>.remote_focus.hardware.name`: not used for device identity or DAQ linkage.
- `microscopes.<microscope>.shutter.hardware.name`: not used.
- `microscopes.<microscope>.shutter.hardware.min` and `.max`: not used by built-in shutter implementations.
- `microscopes.<microscope>.laser.[].type`: `LuxX`/`Obis` top-level laser type is not used; startup derives laser hardware type from `onoff.hardware.type` / `power.hardware.type` and injects a generated `hardware` block.

## Important Evidence

- Default load order is `load_configs()`, then `verify_configuration()`, then `verify_experiment_config()`, then `verify_waveform_constants()` in `src/navigate/controller/controller.py`.
- `verify_configuration()` overwrites `configuration["configuration"]["gui"]` with `{"channels": {"count": channel_count}}`.
- `ConfigurationController.number_of_channels` reads `configuration["gui"]["channel_settings"]["count"]` from `gui_configuration.yml`, not the top-level hardware config.
- `BDVMetadata.get_affine_parameters()` and pyramidal data code read `configuration["experiment"]["BDVParameters"]`, not `configuration["configuration"]["BDVParameters"]`.
- Device hardware keys can be consumed dynamically through `start_device()`, `get_connect_params()`, and base classes, so exact `rg` hits alone under-report usage.

## Leaf-Schema Classification

| Path | Entries | Status | Evidence / rationale |
| --- | ---: | --- | --- |
| `BDVParameters.shear.shear_data` | 1 | Not used | BDV runtime reads `experiment.BDVParameters.shear.shear_data`; this top-level config value is not consulted. |
| `BDVParameters.shear.shear_dimension` | 1 | Not used | Same as above. |
| `BDVParameters.shear.shear_angle` | 1 | Not used | Same as above. |
| `BDVParameters.rotate.rotate_data` | 1 | Not used | Same as above. |
| `BDVParameters.rotate.X` | 1 | Not used | Same as above; rotation angles are read from experiment BDV settings. |
| `BDVParameters.rotate.Y` | 1 | Not used | Same as above. |
| `BDVParameters.rotate.Z` | 1 | Not used | Same as above. |
| `gui.channels.count` | 1 | Not used | Overwritten in `verify_configuration()` before channel validation; GUI count comes from `gui_configuration.yml`. |
| `microscopes.<microscope>.daq.hardware.type` | 2 | Used | Chooses NI/Synthetic/ASI DAQ in `load_devices()` / `start_daq()`. |
| `microscopes.<microscope>.daq.sample_rate` | 2 | Used | Used by DAQ, galvo, remote focus, NI stage timing, and stage/UI helpers. |
| `microscopes.<microscope>.daq.master_trigger_out_line` | 2 | Used | Used by `NIDAQ.create_master_trigger_task()`. |
| `microscopes.<microscope>.daq.camera_trigger_out_line` | 2 | Used | Used by `NIDAQ.create_camera_task()`. |
| `microscopes.<microscope>.daq.trigger_source` | 2 | Used | Used by NI DAQ, NI galvo, NI remote focus, and NI stage. |
| `microscopes.<microscope>.daq.laser_port_switcher` | 2 | Used | Optional NI laser-switching task in `NIDAQ.enable_microscope()`. |
| `microscopes.<microscope>.daq.laser_switch_state` | 2 | Used | Optional NI laser-switching state in `NIDAQ.enable_microscope()`. |
| `microscopes.<microscope>.camera.hardware.type` | 2 | Used | Device class selection and camera comparison. |
| `microscopes.<microscope>.camera.hardware.serial_number` | 2 | Used | Camera ref identity, sequence-device lookup, camera-map menu, same-camera comparison. |
| `microscopes.<microscope>.camera.hardware.camera_connection` | 2 | Possibly used | Required by Photometrics cameras and same-camera comparison, but ignored by default Hamamatsu connection. |
| `microscopes.<microscope>.camera.defect_correct_mode` | 2 | Used | Used by Hamamatsu trigger setup. |
| `microscopes.<microscope>.camera.delay` | 2 | Used | Used for waveform timing and default waveform constants. |
| `microscopes.<microscope>.camera.settle_down` | 2 | Not used | No runtime consumer; runtime checks `settle_duration` and waveform `camera_settle_duration` instead. |
| `microscopes.<microscope>.camera.flip_x` | 2 | Used | Exposed through `ConfigurationController.camera_flip_flags`. |
| `microscopes.<microscope>.camera.flip_y` | 2 | Used | Exposed through `ConfigurationController.camera_flip_flags`. |
| `microscopes.<microscope>.remote_focus.hardware.type` | 2 | Used | Device class selection and autofocus support. |
| `microscopes.<microscope>.remote_focus.hardware.channel` | 2 | Used | NI remote-focus analog output and autofocus device reference. |
| `microscopes.<microscope>.remote_focus.hardware.min` | 2 | Used | Remote focus waveform voltage bounds. |
| `microscopes.<microscope>.remote_focus.hardware.max` | 2 | Used | Remote focus waveform voltage bounds. |
| `microscopes.<microscope>.remote_focus.hardware.port` | 2 | Possibly used | Used by serial remote-focus types such as Equipment Solutions / ASI, not default NI. |
| `microscopes.<microscope>.remote_focus.hardware.baudrate` | 2 | Possibly used | Used by serial remote-focus types, not default NI. |
| `microscopes.<microscope>.remote_focus.hardware.name` | 1 | Not used | Device identity is type/channel; DAQ linkage is passed as the active DAQ connection. |
| `microscopes.<microscope>.galvo.[].hardware.type` | 2 | Used | Device class selection and acquisition shutdown logic. |
| `microscopes.<microscope>.galvo.[].hardware.channel` | 2 | Used | NI galvo analog output channel. |
| `microscopes.<microscope>.galvo.[].hardware.min` | 2 | Used | Galvo waveform voltage bounds. |
| `microscopes.<microscope>.galvo.[].hardware.max` | 2 | Used | Galvo waveform voltage bounds. |
| `microscopes.<microscope>.galvo.[].waveform` | 2 | Used | Galvo waveform generation. |
| `microscopes.<microscope>.galvo.[].phase` | 2 | Used | Galvo sine/sawtooth waveform phase. |
| `microscopes.<microscope>.filter_wheel.hardware.type` | 2 | Used | Device class selection and filter-wheel identity. |
| `microscopes.<microscope>.filter_wheel.hardware.wheel_number` | 2 | Used | Filter-wheel identity, wheel selection, and normalized naming. |
| `microscopes.<microscope>.filter_wheel.hardware.port` | 2 | Used | Serial connection for default Sutter filter wheels. |
| `microscopes.<microscope>.filter_wheel.hardware.baudrate` | 2 | Used | Serial connection for default Sutter filter wheels. |
| `microscopes.<microscope>.filter_wheel.filter_wheel_delay` | 2 | Possibly used | Used by ASI/LUDL/NI filter-wheel implementations; default Sutter implementation ignores it. |
| `microscopes.<microscope>.filter_wheel.available_filters.<filter>` | 20 | Used | Channel validation, channel UI, filter-wheel base dictionary, and filter selection. |
| `microscopes.<microscope>.stage.hardware.[].type` | 3 | Used | Stage class selection; legacy `Thorlabs` is remapped to `KIM001`. |
| `microscopes.<microscope>.stage.hardware.[].serial_number` | 3 | Used | Stage identity and PI/KIM/KINESIS connection parameters. |
| `microscopes.<microscope>.stage.hardware.[].axes.[]` | 10 | Used | Stage axis ownership, UI controls, autofocus setup, movement routing. |
| `microscopes.<microscope>.stage.hardware.[].axes_mapping.[]` | 10 | Used | StageBase hardware-axis mapping; NI/ASI/KIM/PI movement use it. |
| `microscopes.<microscope>.stage.hardware.[].feedback_alignment` | 3 | Possibly used | Used by ASI stages; read by StageBase but no effect for default PI/KIM001. |
| `microscopes.<microscope>.stage.hardware.[].device_units_per_mm` | 3 | Possibly used | Used by KINESIS fallback scaling; not default PI/KIM001. |
| `microscopes.<microscope>.stage.hardware.[].volts_per_micron` | 3 | Possibly used | Used by NI analog stages; not default PI/KIM001. |
| `microscopes.<microscope>.stage.hardware.[].min` | 3 | Possibly used | Used by NI analog stages; not default PI/KIM001. |
| `microscopes.<microscope>.stage.hardware.[].max` | 3 | Possibly used | Used by NI analog stages; not default PI/KIM001. |
| `microscopes.<microscope>.stage.hardware.[].distance_threshold` | 3 | Possibly used | Used by NI analog stage wait behavior; not default PI/KIM001. |
| `microscopes.<microscope>.stage.hardware.[].settle_duration_ms` | 3 | Possibly used | Used by NI analog stage wait behavior; not default PI/KIM001. |
| `microscopes.<microscope>.stage.hardware.[].controllername` | 3 | Used | Required by PI stage connection; blank non-PI occurrences are not used. |
| `microscopes.<microscope>.stage.hardware.[].stages` | 3 | Used | Required by PI stage startup; blank non-PI occurrences are not used. |
| `microscopes.<microscope>.stage.hardware.[].refmode` | 3 | Used | Required by PI stage startup; blank non-PI occurrences are not used. |
| `microscopes.<microscope>.stage.hardware.[].port` | 3 | Possibly used | Used by serial stage types such as Sutter/Newport/Conex; not default PI/KIM001. |
| `microscopes.<microscope>.stage.hardware.[].baudrate` | 3 | Possibly used | Used by serial stage types; not default PI/KIM001. |
| `microscopes.<microscope>.stage.hardware.[].timeout` | 3 | Possibly used | Used by serial stage factory; not default PI/KIM001. |
| `microscopes.<microscope>.stage.joystick_axes.[]` | 6 | Used | Stage controller toggles joystick button and mode from this list. |
| `microscopes.<microscope>.stage.x_min` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.x_max` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.y_min` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.y_max` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.z_min` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.z_max` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.f_min` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.f_max` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.theta_min` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.theta_max` | 2 | Used | Stage limits through `ConfigurationController.get_stage_position_limits()`. |
| `microscopes.<microscope>.stage.x_offset` | 2 | Used | Stage offset compensation when switching resolutions and volume-search targeting. |
| `microscopes.<microscope>.stage.y_offset` | 2 | Used | Same as above. |
| `microscopes.<microscope>.stage.z_offset` | 2 | Used | Same as above. |
| `microscopes.<microscope>.stage.theta_offset` | 2 | Used | Used through axis-derived stage offset helpers when theta is active. |
| `microscopes.<microscope>.stage.f_offset` | 2 | Used | Used through axis-derived stage offset helpers when focus axis is active. |
| `microscopes.<microscope>.stage.flip_x` | 2 | Used | Stage flip flags for UI/channel position behavior. |
| `microscopes.<microscope>.stage.flip_y` | 2 | Used | Stage flip flags for UI/channel position behavior. |
| `microscopes.<microscope>.stage.flip_z` | 2 | Used | Stage flip flags for UI/channel position behavior. |
| `microscopes.<microscope>.stage.flip_f` | 2 | Used | Stage flip flags for focus-axis behavior. |
| `microscopes.<microscope>.zoom.hardware.type` | 2 | Used | Zoom device class selection; synthetic occurrence is ignored after type selection. |
| `microscopes.<microscope>.zoom.hardware.servo_id` | 2 | Used | Dynamixel device identity and runtime servo ID; synthetic occurrence is ignored. |
| `microscopes.<microscope>.zoom.hardware.port` | 2 | Used | Dynamixel serial connection for Mesoscale; synthetic occurrence is ignored. |
| `microscopes.<microscope>.zoom.hardware.baudrate` | 2 | Used | Dynamixel serial connection for Mesoscale; synthetic occurrence is ignored. |
| `microscopes.<microscope>.zoom.position.<zoom>` | 8 | Used | Zoom menu, default microscope state, waveform constants validation, and zoom hardware movement. |
| `microscopes.<microscope>.zoom.pixel_size.<zoom>` | 8 | Used | OME metadata, ASI stage tuning, FOV calculations, and volume-search resolution math. |
| `microscopes.<microscope>.zoom.stage_positions.<solvent>.<axis>.<zoom>` | 8 | Used | `ZoomBase.build_stage_dict()` builds inter-zoom focus offsets from these values. |
| `microscopes.<microscope>.shutter.hardware.type` | 2 | Used | Shutter device class selection. |
| `microscopes.<microscope>.shutter.hardware.channel` | 2 | Used | NI shutter output channel. |
| `microscopes.<microscope>.shutter.hardware.min` | 2 | Not used | No built-in shutter implementation reads shutter voltage min. |
| `microscopes.<microscope>.shutter.hardware.max` | 2 | Not used | No built-in shutter implementation reads shutter voltage max. |
| `microscopes.<microscope>.shutter.hardware.name` | 1 | Not used | Not used for device identity or DAQ linkage. |
| `microscopes.<microscope>.laser.[].wavelength` | 6 | Used | Laser identity, channels, waveform constants, device refs, and UI labels. |
| `microscopes.<microscope>.laser.[].onoff.hardware.type` | 6 | Used | Laser hardware block generation and NI/ASI modulation selection. |
| `microscopes.<microscope>.laser.[].onoff.hardware.channel` | 6 | Used | NI digital modulation output. |
| `microscopes.<microscope>.laser.[].onoff.hardware.min` | 6 | Used | NI digital/analog output bounds when applicable. |
| `microscopes.<microscope>.laser.[].onoff.hardware.max` | 6 | Used | NI digital/analog output bounds when applicable. |
| `microscopes.<microscope>.laser.[].power.hardware.type` | 6 | Used | Laser hardware block generation and NI/ASI modulation selection. |
| `microscopes.<microscope>.laser.[].power.hardware.channel` | 6 | Used | NI analog modulation output. |
| `microscopes.<microscope>.laser.[].power.hardware.min` | 6 | Used | NI analog output bounds. |
| `microscopes.<microscope>.laser.[].power.hardware.max` | 6 | Used | NI analog output bounds. |
| `microscopes.<microscope>.laser.[].type` | 6 | Not used | Top-level `LuxX`/`Obis` field is never read; startup uses `onoff.hardware.type` / `power.hardware.type` instead. |

## Container Entries

All structural containers under `microscopes.<microscope>` are used to iterate microscopes and devices, including `daq`, `camera`, `remote_focus`, `galvo`, `filter_wheel`, `stage`, `zoom`, `shutter`, `laser`, and their `hardware` subcontainers.

The two container families that are not used as packaged are:

- `BDVParameters`, `BDVParameters.shear`, `BDVParameters.rotate`
- `gui`, `gui.channels` as shipped in `configuration.yaml`; `verify_configuration()` replaces this family before downstream channel validation.

## Recommended Cleanup Order

1. Remove or relocate top-level `BDVParameters` from `configuration.yaml`; keep BDV defaults in experiment/acquisition-save settings if defaults are needed.
2. Remove `gui.channels.count` from `configuration.yaml` or make `verify_configuration()` preserve a documented source of truth.
3. Replace or remove `camera.settle_down`; if the intended behavior is camera settling, standardize on the actually read key (`settle_duration`) or waveform `camera_settle_duration`.
4. Remove `remote_focus.hardware.name` and `shutter.hardware.name` from the packaged defaults.
5. Remove `shutter.hardware.min` / `max` unless a built-in shutter implementation is updated to consume them.
6. Remove `laser.[].type` or wire it into laser startup if the LuxX/Obis distinction is still meaningful.
7. For stage hardware entries, consider device-specific example blocks instead of putting every possible stage field on every stage. Many fields are valid schema but irrelevant for the default PI/KIM001 stages.
