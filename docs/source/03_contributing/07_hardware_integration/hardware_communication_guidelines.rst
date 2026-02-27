.. _hardware_communication_guidelines:

=========================================
Hardware Communication Guidelines
=========================================

This page covers concurrency and interface requirements for hardware integrations.

Threads and Blocking
====================

Hardware communication is often sequential and stateful. When multiple threads read and write to the same resource (for example, one serial line), interleaving calls can corrupt communication.

To reduce communication errors:

- Prefer one dedicated communication thread per hardware device.
- Avoid overlapping reads and writes on shared ports.
- Use explicit synchronization primitives (for example, ``threading.Event``) when access must be serialized.
- Keep handshaking and command/response ordering deterministic.

Dedicated Device Interfaces
===========================

**navigate** uses a hardware abstraction layer with dedicated interfaces per device type.

When integrating new hardware:

- Implement the correct base class for the target device type (camera, stage, laser, and so on).
- Implement all required abstract methods from the base class.
- Keep device-specific behavior inside the device class while preserving shared interface semantics.

This pattern keeps behavior consistent across vendors and reduces integration errors.

For a step-by-step implementation workflow, see :ref:`Add a New Hardware Device <add_new_hardware_device>`.
