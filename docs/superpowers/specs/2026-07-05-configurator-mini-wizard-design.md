# Configurator Mini Wizard Design

Date: 2026-07-05

## Context

The Navigate configuration assistant currently renders each hardware tab from flat
widget dictionaries in `src/navigate/config/configuration_database.py`. The view in
`src/navigate/view/configurator_application_window.py` builds all widgets for a
hardware category at once, and `src/navigate/controller/configurator.py` saves by
walking each tab's `variables_list`.

This makes the configurator comprehensive, but difficult for new users. It shows
fields for all supported devices even when those fields do not apply to the
selected device type. Existing helper text is sparse and often appears as a
single right-side label, so users have to infer which fields are required,
recommended, advanced, or device-specific.

The goal is to improve the configurator for both new users and expert users
without replacing the YAML format or maintaining two separate configurator
interfaces.

## Approved Direction

Use a mini wizard inside each hardware tab.

The configurator keeps the existing high-level structure:

- microscope tabs remain the top-level grouping
- hardware tabs remain inside each microscope
- Save and Load continue to operate on Navigate YAML configuration files
- the existing widget catalog remains the primary source of field definitions

Each hardware tab becomes a guided, flexible mini wizard. Steps organize the
form, but users can jump between steps freely. Basic mode is the default.
Advanced mode exposes expert and device-specific fields without creating a
separate interface.

## Scope

The first implementation should provide the shared mini-wizard shell for every
hardware tab, then fully wire device-specific behavior for these pilot tabs:

- Camera
- Data Acquisition Card
- Stages

The remaining tabs should receive the shared step/header/help-panel shell in the
first pass, but they do not need full device-specific metadata until later:

- Filter Wheel
- Galvo
- Lasers
- Remote Focus Devices
- Adaptive Optics
- Shutters
- Zoom Device

This keeps the UI coherent while limiting the first PR's metadata and validation
surface.

## User Experience

Each hardware tab should present three areas:

- a step navigator
- the fields for the selected step
- contextual help and examples

The step navigator is clickable. It guides users through the tab but does not
lock them into a strict sequence.

Basic mode shows required and recommended fields that apply to the selected
device type. Fields that do not apply to the selected device type are hidden
from Basic mode. They are still accessible in Advanced mode when appropriate.

Advanced mode exposes advanced fields, optional fields, device-specific fields,
and preserved loaded values. Advanced mode should make expert access obvious,
but Basic mode should remain uncluttered for users configuring Navigate for the
first time.

When Basic mode hides fields, the UI may show a concise note such as "4
advanced/device-specific fields hidden" where it helps users understand that
additional fields exist.

## Field Metadata

Keep the existing widget definitions compatible with the current renderer during
migration. Add a metadata layer that can coexist with the current list-based
field specs.

The metadata should describe:

- step membership
- field importance: required, recommended, optional, or advanced
- device applicability
- short inline hint text
- longer help-panel text and examples
- validation rules
- whether hidden loaded values should be preserved

The first implementation should avoid hard-coding Camera, DAQ, or Stage behavior
directly into Tk view logic. Device-specific behavior should be expressed in the
metadata layer and interpreted by shared filtering and validation helpers.

If metadata is missing or invalid for a field, the conservative fallback is to
show the field rather than hide it silently.

## Suggested Pilot Step Groupings

Camera:

- Device Type
- Connection
- Timing
- Orientation
- Review

Data Acquisition Card:

- Device Type
- Timing
- Triggering
- Laser Switching
- Review

Stages:

- Device Type
- Axes
- Motion Limits
- Controller Settings
- Advanced
- Review

These groupings can be refined during implementation, but the first PR should
keep each pilot tab small enough for users to understand what to do next.

## Save And Load Behavior

Loaded configurations may contain fields that Basic mode hides. Those hidden
loaded values must be preserved unless the user changes the relevant device
type.

On save, the configurator should merge visible edited values with preserved
hidden loaded values. This prevents Basic mode from destructively dropping valid
expert configuration data.

If the user changes a device type, stale fields from the previous device type
should not be silently carried forward. The configurator should keep the UI
non-destructive while editing, then warn on save before removing stale fields
from the previous device type.

Unknown values loaded from existing files should be preserved when the
configurator can associate them with the current hardware block. This protects
future or hand-authored configuration keys that are not represented in the UI
yet.

## Validation

Validation should be inline and non-blocking.

Missing or malformed required fields should be shown in the relevant step.
Hardware tabs and steps should use restrained warning indicators so users can
find incomplete areas before saving.

Save should remain possible. If unresolved required-field warnings remain, the
save flow should summarize them before writing the YAML file, rather than
failing without explanation.

Validation should be testable separately from the Tk rendering where practical.

## Components

`src/navigate/config/configuration_database.py`

- remains the primary catalog for configurator fields
- gains the wizard metadata layer
- defines Camera, DAQ, and Stage applicability and validation metadata first
- keeps existing field specs compatible during migration

`src/navigate/view/configurator_application_window.py`

- renders hardware tabs as mini-wizard surfaces
- builds step navigation, Basic/Advanced controls, field groups, and help panels
- filters visible fields by current step, mode, selected device type, and
  metadata
- keeps exposing enough variable state for the controller to save values

`src/navigate/controller/configurator.py`

- continues coordinating new, load, save, and add-microscope actions
- tracks loaded hidden values that should be preserved
- merges preserved hidden values with visible edited values during save
- handles or warns about stale values after a device type change

`src/navigate/controller/configuration_controller.py`

- should remain lightly touched unless implementation reveals a need for shared
  config-derived helpers

## Testing

Add focused tests for:

- Basic vs Advanced visibility filtering
- device-specific field visibility for Camera, DAQ, and Stages
- required and malformed field validation
- load/save round trips that preserve hidden loaded values
- device type changes that do not silently carry stale previous-device fields
- non-pilot tabs still rendering and saving through the shared shell

Tk rendering tests should stay pragmatic. Pure metadata, filtering, validation,
and save/load merge behavior should be tested outside Tk where possible.

## Non-Goals

This design does not require:

- replacing Tk
- changing Navigate's YAML configuration schema
- building a full cross-hardware setup wizard
- completing device-specific metadata for every hardware tab in the first PR
- removing expert access to advanced fields

## Planning Defaults

The implementation plan should start from these defaults:

- represent field metadata as dictionaries keyed by the existing field path,
  using explicit keys such as `step`, `importance`, `applies_to`, `hint`, `help`,
  `validators`, and `preserve_hidden`
- when a device type changes, keep the UI non-destructive while editing, then
  warn on save before removing stale fields from the previous device type
- use compact text warning badges in tab and step labels so the design does not
  depend on new image assets or theme-specific icons
- preserve the existing `variables_list` save path for visible fields and add a
  merge layer for hidden loaded values rather than rewriting serialization in
  the first PR
