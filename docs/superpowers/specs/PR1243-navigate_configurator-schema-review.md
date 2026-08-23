# Configurator schema property review

This note lists the property names currently added to the configurator schema.
Shared base-class properties apply to every selected device that inherits from
that base class.

**Flag meanings:** **Required** fields are accessed without a runtime fallback.
**Optional** fields have a safe fallback or enable an optional feature.
**Conditional** fields are required only for the selected hardware implementation
or subcomponent identified in the note.

## Shared device bases

- `SerialDevice`
  - `port` — **Required** for a physical serial device
  - `baudrate` — **Optional** (defaults to 115200)
  - `timeout` — **Optional** (defaults to 0.25 seconds)
- `SequenceDevice`
  - `serial_number` — **Required** to select a physical sequence device

## Cameras

- `CameraBase` (shared by all cameras)
  - `flip_x` — **Optional** (defaults to `False`)
  - `flip_y` — **Optional** (defaults to `False`)
  - `pixel_size_in_microns` — **Optional** (defaults to 6.5 µm; hardware may override it)
- `PhotometricsCamera`
  - `readout_port` — **Optional** (defaults to 0)
  - `speed_table_index` — **Optional** (defaults to 1)
  - `gain` — **Optional** (defaults to 1)
  - `unitforlinedelay` — **Optional** (defaults to 1)
  - Existing connection property supplied by `get_connect_params()`:
    `camera_connection` — **Required**
- `HamamatsuBase` (inherited by the selectable Hamamatsu camera classes)
  - `defect_correct_mode` — **Required**
  - Inherited from `SequenceDevice`: `serial_number` — **Required**
- `SyntheticCamera`
  - `x_pixels` — **Optional** (defaults to 2048)
  - `y_pixels` — **Optional** (defaults to 2048)
- `DahengCamera`
  - `serial_number` — **Optional** (an unspecified serial number selects the
    default camera)
- `MU196XRCamera`
  - `input_trigger_port` — **Optional** (defaults to 2; saved as a number and
    mapped to `XI_GPI_PORT<i>` by the driver)

## DAQs

- `DAQBase` (shared by all DAQs)
  - `sample_rate` — **Required**
- `NIDAQ`
  - `trigger_source` — **Required**
  - `master_trigger_out_line` — **Required**
  - `camera_trigger_out_line` — **Required**
  - `laser_port_switcher` — **Optional**
  - `laser_switch_state` — **Optional**
  - `trigger_reset_count` — **Optional** (disabled when absent or zero)
- `ASIDaq`
  - Inherited from `SerialDevice`: `port` — **Required**; `baudrate` and
    `timeout` — **Optional**
- `SyntheticDAQ`
  - No type-specific properties; inherits `sample_rate` from `DAQBase`.

## Filter wheels

- `FilterWheelBase` (shared by all filter wheels)
  - `name` — **Optional**
  - `hardware/wheel_number` — **Required**
  - `filter_wheel_delay` — **Required**
  - `available_filters` (a repeatable collection with `name` and `position`
    per filter) — **At least one required**; each added `name` and `position`
    is **Required**
- `NIFilterWheel`
  - Overrides `available_filters` so each filter has a `name` and its
    `channel` (NI DAQ channel name), instead of a numeric position. **At least
    one filter is required**; each added `name` and `channel` is **Required**.

## Galvos

- `GalvoBase` (shared by all galvos)
  - `waveform` — **Optional** (defaults to `sawtooth`)
  - `phase` — **Required**
  - `hardware/min` — **Required**
  - `hardware/max` — **Required**
- `NIGalvo`
  - `hardware/channel` — **Required**
- `ASIGalvo`
  - `hardware/axis` — **Required**
- Legacy `amplitude`, `offset`, `rising_ramp`, and `frequency` entries under a
  galvo are only read while migrating older configurations. Current waveform
  settings belong in `waveform_constants.galvo_constants`, so they are not
  device-schema properties.

## Lasers

- `LaserBase` (shared by all lasers)
  - `wavelength` — **Required**
  - `power/hardware/type` — **Required**
  - `onoff/hardware/type` — **Required**
  - `power/hardware/min`, `power/hardware/max` — **Conditional** (required
    when power is controlled by NI or ASI)
  - `onoff/hardware/min`, `onoff/hardware/max` — **Conditional** (required
    when on/off is controlled by NI or ASI)
- `NILaser`
  - `power/hardware/channel` — **Conditional** (when power type is NI)
  - `onoff/hardware/channel` — **Conditional** (when on/off type is NI)
- `ASILaser`
  - Inherited from `SerialDevice`: `port` — **Required**; `baudrate` and
    `timeout` — **Optional**
  - `power/hardware/axis` — **Conditional** (when power type is ASI)
  - `onoff/hardware/axis` — **Conditional** (when on/off type is ASI)
- `SyntheticLaser`
  - No type-specific properties; inherits `wavelength` from `LaserBase`.
- The top-level laser `hardware` mapping is a compatibility projection derived
  from the selected power/on-off hardware and `wavelength`; it is not an
  independently editable schema property.

## Mirrors

- `MirrorBase`
  - No shared, editable configuration properties beyond the device's generic
    `hardware/type`.
- `ImagineOpticsMirror`
  - `hardware/flat_path` — **Required**
- `SyntheticMirror`
  - No schema properties added.
- Legacy `n_modes` entries are not read from the mirror configuration. The
  adaptive-optics feature obtains the mode count from the mirror controller.

## Pumps

- `PumpBase`
  - No shared pump-specific properties. Connection settings are inherited from
    the device communication base class.
- `XCaliburPump`
  - Inherited from `SerialDevice`: `port` — **Required**; `baudrate` and
    `timeout` — **Optional**
  - `min_speed_code` — **Optional** (defaults to 0)
  - `max_speed_code` — **Optional** (defaults to 40)
  - `fine_positioning` — **Optional** (defaults to `False`)

## Remote-focus devices

- `RemoteFocusBase` (shared by all remote-focus devices)
  - `hardware/min` — **Required**
  - `hardware/max` — **Required**
- `NIRemoteFocus`
  - `hardware/channel` — **Required**
- `ASIRemoteFocus`
  - Inherited from `SerialDevice`: `port` — **Required**; `baudrate` and
    `timeout` — **Optional**
  - `hardware/axis` — **Required**
- `EquipmentSolutionsRemoteFocus`
  - Inherits the `RemoteFocusBase` voltage and waveform-control settings.
  - `hardware/channel` — **Required**
  - Inherited from `SerialDevice`: `port` — **Required**; `baudrate` and
    `timeout` — **Optional**
- `EquipmentSolutionsASIRemoteFocus`
  - Inherits the `RemoteFocusBase` voltage and waveform-control settings.
  - `hardware/axis` — **Required**
  - Inherited from `SerialDevice`: `port` — **Required**; `baudrate` and
    `timeout` — **Optional**
- `SyntheticRemoteFocus`
  - No type-specific properties; inherits the `RemoteFocusBase` voltage and
    waveform-control settings.
- Legacy remote-focus `amplitude` and `offset` entries are only used while
  migrating old configurations. Current waveform values belong in
  `waveform_constants.remote_focus_constants`, so they are not
  device-schema properties.

## Shutters

- `ShutterBase`
  - No shared, editable configuration properties beyond the generic
    `hardware/type`.
- `NIShutter`
  - `hardware/channel` — **Required**
- `ASIShutter`
  - Inherited from `SerialDevice`: `port` — **Required**; `baudrate` and
    `timeout` — **Optional**
  - `hardware/axis` — **Required**
- `SyntheticShutter`
  - No schema properties added.
- Legacy/sample shutter `hardware/min`, `hardware/max`, and `hardware/name`
  entries are not read by shutter runtime code, so they are not device-schema
  properties.

## Stages

- `StageBase` (shared by all stages)
  - `axes` — **Required**
  - `axes_mapping` — **Optional** (the device uses its default mapping when absent)
  - `joystick_axes` — **Optional** (saved as a list of axes)
  - For every axis entered in `axes`, the configurator adds `<axis>_min`,
    `<axis>_max`, and `flip_<axis>` (for example, `x_min`, `x_max`, and
    `flip_x`). `<axis>_min` and `<axis>_max` are **Required**; `flip_<axis>`
    is **Optional** (defaults to `False`). These are written alongside the
    stage `hardware` list.
- `NIStage`
  - `volts_per_micron` — **Required**
  - `min` — **Required**
  - `max` — **Required**
  - `distance_threshold` — **Optional**
  - `settle_duration_ms` — **Optional** (defaults to 20 ms)
- `MS2000Stage`
  - Inherited from `ASIStage`: `feedback_alignment` — **Optional**
  - `jsspd` — **Optional** (ASI wheel jog speed)
- `ASIStage` and `MFC2000Stage`
  - `feedback_alignment` — **Optional**
- `KST101Stage`
  - Existing connection property from `get_connect_params()`: `serial_number`
    — **Required**
  - `device_units_per_mm` — **Optional** (defaults to 1000)
- `KINESISStage`
  - Existing connection property from `get_connect_params()`: `serial_number`
    — **Required**
  - `steps_per_um` — **Optional** (defaults to 1)
  - Legacy `device_units_per_mm` is still read as a fallback when
    `steps_per_um` is absent, but is not the current editable setting.
- Serial stage implementations (`ASIStage`, `MFC2000Stage`, `ConexStage`,
  `NewportStage`, and `MP285Stage`)
  - Inherited from `SerialDevice`: `port` — **Required**; `baudrate` and
    `timeout` — **Optional**
- `PIStage`
  - Existing connection properties from `get_connect_params()`:
    `controllername`, `serial_number`, `stages`, `refmode` — **Required**
- `MCLStage` and `KIM001Stage`
  - Existing connection property from `get_connect_params()`: `serial_number`
    — **Required**
- `SyntheticStage`
  - No type-specific properties; inherits the `StageBase` properties.
- The following are microscope-level stage behavior, rather than settings of an
  individual stage hardware entry, so the current device Property/Value editor
  does not attach them to a selected stage: `position` (`x_pos`, `y_pos`,
  `z_pos`, `theta_pos`, and `f_pos`), `coupled_axes`, `has_ni_galvo_stage`,
  and per-axis `<axis>_step`, `<axis>_offset`, and
  `<axis>_home`. Per-axis `<axis>_min`, `<axis>_max`, and `flip_<axis>` are
  handled specially by the configurator and saved alongside `stage.hardware`.

## Zoom devices

- `ZoomBase` (shared by all zoom devices)
  - `zoom_values` (one repeatable row per zoom: device `position` and
    `pixel_size`; saved as the existing two YAML mappings) — **Optional**;
    saving an empty collection creates the default `N/A` calibration. Each
    `zoom`, `position`, and `pixel_size` row field is **Required**.
  - `stage_positions` (repeatable solvent, stage-axis, zoom, and position
    calibration rows; used to calculate stage offsets when changing zoom) —
    **Optional** collection; each added row field is **Required**
- `DynamixelZoom`
  - Inherited from `SerialDevice`: `port` — **Required**; `baudrate` and
    `timeout` — **Optional**
  - `hardware/servo_id` — **Required**
- `SyntheticZoom`
  - No type-specific properties; inherits the `ZoomBase` collections.
