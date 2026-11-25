# Device integration guide

Read the repository root `AGENTS.md` as well as this guide.

## Startup and connection factories

- Device startup is centralized in `../device_startup_functions.py`.
  `start_device()` selects the appropriate factory using the marker classes in
  `device_types.py`: `SerialDevice`, `IntegratedDevice`, `SequenceDevice`,
  `NIDevice`, and `ASIDevice`. Check this path before adding device constructors.
- A physical device may be referenced by several microscope definitions.
  Reuse the existing factories instead of opening an independent connection in
  each microscope. Keep microscope-specific configuration and metadata separate
  from the shared hardware connection.
- `SerialConnectionFactory.build_connection()` retains the legacy serial-device
  path. Optional laser settings use `acquire_connection()` and counted leases:
  compatible owners share one protocol adapter, and the last lease closes and
  evicts it. Do not close a shared adapter from an individual microscope.
- Shared serial identities must account for port aliases and compatible protocol,
  baud rate, and timeout settings. Reject incompatible owners before opening or
  reconfiguring a port. Never reuse a laser connection as an unrelated device.
- Share the protocol transaction lock, not just the raw serial port. Hold it
  across command, acknowledgement, verification, and associated metadata reads.
  Per-wrapper locks do not protect a shared physical connection.
- Invalidate cached hardware state across every owner after writes and failed
  transactions. The laser settings session uses revisions so stale power values
  cannot be reused for gating or published as current confirmations.
- Handle initialization failures, partial construction, repeated shutdown, last
  owner release, and reopening. Preserve the original error when retries fail.

## Device contracts and compatibility

- Keep acquisition timing/gating separate from optional software configuration.
  Adding serial laser settings must preserve NI/ASI electrical behavior.
- Use an ABC for required capabilities and explicit capability reporting for
  optional operations. Do not invent readbacks for unsupported hardware.
- Missing optional configuration entries must preserve existing behavior. Virtual
  Devices mode must not open physical connections.
- Keep blocking hardware I/O in the model process/workers, off the Tk main thread.
  Read the controller README before modifying controller-facing behavior.

## Validation

- Test connection reuse, concurrent transactions, conflicting settings, cleanup,
  cross-owner cache invalidation, and old configurations using emulators/mocks.
- Mark tests requiring physical devices or vendor hardware environments with
  `pytest.mark.hardware`. `pytest.ini` excludes them by default. Emulated protocol
  tests belong in normal CI; avoid short wall-clock deadlines in those tests.
- Use explicit `-m hardware` for physical tests. Do not compete with a running
  application for a port. Restore device settings after authorized hardware tests
  and report physical results separately from synthetic or mocked results.
