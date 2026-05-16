.. _software-architecture-developer-concepts:

========================================
Developer Architecture Concepts
========================================

This page captures implementation details that are important for developers working in the **navigate** codebase. Each section is intentionally short so teams can keep, merge, or remove entries as this architecture evolves.

Hardware Integration Deep Dives
-------------------------------

For hardware-focused implementation guidance, use these companion pages:

- :doc:`Hardware Integration Overview <../07_hardware_integration/hardware_integration>`
- :doc:`Hardware Communication Guidelines <../07_hardware_integration/hardware_communication_guidelines>`
- :doc:`How to Add a New Device <../07_hardware_integration/add_new_device>`
- :doc:`Hardware Integration Advanced Notes <../07_hardware_integration/advanced>`

Process and Inter-Process Communication
---------------------------------------

Controller-Model Process Boundary
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The main GUI process owns :class:`Controller` (:file:`src/navigate/controller/controller.py`) and runs Tk, while :class:`Model` (:file:`src/navigate/model/model.py`) is created in a separate process. This split keeps hardware I/O and acquisition work away from Tk event handling, which is required for responsive GUI behavior. New developer features should preserve this boundary unless there is a strong reason to change it.

ObjectInSubprocess Remote-Call Contract
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`ObjectInSubprocess` in :file:`src/navigate/model/concurrency/concurrency_tools.py` makes subprocess method calls look local, but each call is still a pipe round-trip. It uses a non-blocking pipe lock and raises a :class:`RuntimeError` when two threads try to talk to the same proxy at once, which is an intentional safety behavior. This contract is central to understanding many stop-path and concurrency edge cases.

Forced ``spawn`` Multiprocessing Start Method
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The concurrency layer forces multiprocessing start method ``spawn`` in :file:`src/navigate/model/concurrency/concurrency_tools.py`. That keeps behavior consistent across platforms and avoids ``fork``-specific issues with GUI state, hardware handles, and child-process initialization. Any future multiprocessing work should assume ``spawn`` semantics.

Shared Configuration Through ``multiprocessing.Manager``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Configuration is loaded into manager-backed proxy objects (:class:`DictProxy` and :class:`ListProxy`) by :func:`load_configs` and :func:`build_nested_dict` in :file:`src/navigate/config/config.py`. Because both controller and model see the same proxy-backed configuration tree, runtime config edits are visible across process boundaries without manual serialization. This is convenient, but it also means developers must be careful about mutation order and type normalization.

Event Queue Contract (``event_queue``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The model emits typed events to the controller through ``event_queue`` (for example ``warning``, ``update_stage``, ``frame_rate``, ``waveform``, and plugin-defined events). The controller drains this queue in its event pump and routes payloads to UI updates or registered listeners in :file:`src/navigate/controller/controller.py`. When adding new events, define payload shape clearly and keep handler work lightweight.

Image Pipe Contract (``show_img_pipe``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Image display uses a dedicated pipe where the model sends frame IDs and a ``"stop"`` sentinel, while the image data itself stays in shared memory. This keeps transfer overhead small and avoids queueing full arrays across processes. Additional virtual microscopes follow the same pattern with per-microscope pipes.

Shared Memory, Threads, and Error Propagation
----------------------------------------------

``SharedNDArray`` and Shared Memory Ownership
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``SharedNDArray`` in :file:`src/navigate/model/concurrency/concurrency_tools.py` subclasses ``numpy.ndarray`` and carries a shared-memory handle plus custom pickle/reduction behavior. The creator process is responsible for unlinking shared memory, while consumer processes attach by shared-memory name. Developers should close and unlink buffers intentionally during reallocation or teardown to avoid leaked OS-level shared memory segments.

Data Buffer Reallocation and Geometry Changes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Buffer shape changes are negotiated through ``Controller.update_buffer()`` and ``Model.get_data_buffer()/update_data_buffer()``. Old handles are closed (and in the model also unlinked) before new frame buffers are allocated and connected to microscopes. Any code that caches array references across camera-geometry changes can silently break if this lifecycle is not respected.

Signal Thread vs Data Thread in the Model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Acquisition in the model splits into a signal thread (hardware sequencing, waveform-related feature execution) and a data thread (camera frame retrieval, data container calls, optional saving). This separation is key for keeping hardware command cadence and data handling decoupled. The ``is_data_thread_on`` path for some modes changes timing behavior and is an important branch for debugging.

Pause/Resume Data Thread Handshake
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``pause_data_thread()`` and ``resume_data_thread()`` use ``ask_to_pause_data_thread``, ``pause_data_ready_lock``, and ``pause_data_event`` to coordinate a safe pause point in the data loop. This lets feature or update paths block data handling while device state changes complete. It is safer than ad hoc sleeps and should be preferred when cross-thread ordering matters.

User-Visible Exception Bubbling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Exceptions intended for end users are represented by :class:`UserVisibleException` (:file:`src/navigate/model/utils/exceptions.py`). These are captured in model thread wrappers and feature containers, converted to ``("warning", message)`` events, and finally shown via message dialogs in the controller event pump. This gives developers a standard route for actionable user-facing failures without exposing raw tracebacks in the GUI.

Thread-Safe Logging Across Processes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Logging uses a queue/listener pattern set up in :file:`src/navigate/log_files/log_functions.py` so subprocess logs are serialized through a central listener. This keeps logs coherent across controller and model processes and enables reliable performance diagnostics. When adding high-frequency logs, prefer structured and rate-limited entries to keep log volume manageable.

GUI Threading and Latency Control
---------------------------------

Main-Thread Dispatcher and Event Pump
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Controller method ``_run_on_main_thread`` plus ``_schedule_event_pump`` in :file:`src/navigate/controller/controller.py` form the core Tk-thread dispatch system. Background threads enqueue callables, and the Tk loop executes them predictably at short intervals. GUI updates that bypass this pathway can produce race conditions or hard-to-reproduce Tk errors.

Tk Off-Main-Thread Guard
^^^^^^^^^^^^^^^^^^^^^^^^
``install_tk_thread_guard`` in :file:`src/navigate/tools/tk_thread_guard.py` patches core Tk calls to log off-main-thread access with sampled stack traces. It is enabled for runtime safety and can be disabled in specific environments (for example, test contexts) via environment variables. This guard is a diagnostic tool, not a substitute for proper dispatch design.

Resource-Scoped Thread Scheduling in Controller
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The controller uses :class:`SynchronizedThreadPool` (:file:`src/navigate/controller/thread_pool.py`) to serialize thread execution per named resource such as ``model`` or ``camera``. This reduces cross-command interference and provides a predictable command queue model at the controller layer. New long-running controller actions should be assigned to the right resource to avoid contention.

``sloppy_stop`` and Stop-Path Contention
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``sloppy_stop`` in :file:`src/navigate/controller/controller.py` is explicitly marked as a temporary workaround that repeatedly tries to send ``stop`` until it wins contention. It relies on ``ObjectInSubprocess`` lock behavior rather than explicit queue preemption, which is effective but brittle. Any stop-path refactor should replace this with a first-class interruption strategy.

Live-Mode Frame Dropping to Prevent Display Lag
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In live mode, the controller drains queued frame IDs and keeps only the most recent frame before rendering. This intentionally drops stale frames to bound display latency, which is usually preferable to showing every frame late. Developers should treat this as a real-time UX decision, not a data-loss bug.

Coalesced Camera Display Updates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Camera view updates use ``after_idle`` coalescing in :file:`src/navigate/controller/sub_controllers/camera_view.py`, where “latest frame wins” between idle cycles. Together with max-FPS throttling, this prevents render backlog from growing unbounded under high acquisition rates. This pattern is a key reason the GUI remains responsive when cameras outpace display.

Persistent ``PhotoImage`` and In-Place Paste
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The camera view keeps a persistent ``PhotoImage`` and updates it with in-place ``paste`` instead of recreating Tk image objects per frame. This minimizes Tk object churn and significantly reduces frame-display overhead. Developers changing display code should preserve this memory and object-reuse strategy.

Histogram Coalescing and Statistical Downsampling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Histogram updates in :file:`src/navigate/controller/sub_controllers/histogram.py` are also coalesced with ``after_idle`` and operate on downsampled pixel subsets. The downsampling target is chosen from bin count and desired accuracy, which limits compute cost while preserving useful distribution shape. This is a deliberate latency-vs-fidelity tradeoff that should remain explicit.

Performance Telemetry and Diagnostics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The codebase defines a custom ``PERFORMANCE`` log level and uses ``performance_monitor`` decorators for hot paths like image display and histogram rendering. The diagnostics popup loads and summarizes these logs into histograms for acquisition, rendering, stage, DAQ, and serial timings. This creates an internal performance feedback loop that developers can use before profiling with external tools.

Stage Position Caching Policy for Latency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
``Microscope.set_stage_position_cache_policy`` enables cached stage positions for ``z-stack`` and ``customized`` modes in :file:`src/navigate/model/microscope.py`. This avoids repeated hardware position queries in tight loops, which the code comments identify as expensive. The tradeoff is potentially stale positions between explicit refresh points, so cache policy must match acquisition semantics.

Known High-Impact Bottlenecks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Current architecture and telemetry point to a few recurring bottlenecks: image rendering, histogram generation, stage-position polling, and serial communication overhead. These areas are already instrumented and have dedicated mitigation patterns (coalescing, throttling, caching, batching). Performance changes should start by measuring these paths first instead of broad refactors.

Feature Execution Model
-----------------------

Feature Container as Signal/Data Trees
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The feature system builds parallel signal and data trees from feature definitions in :file:`src/navigate/model/features/feature_container.py`. Signal nodes coordinate hardware-side behavior, while data nodes process frame IDs from acquisition. This split lets one feature list express both device orchestration and image/data logic.

``config_table`` Interface Contract
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Each feature object exposes a ``config_table`` with ``signal``, ``data``, and optional ``node`` metadata. Default handlers are filled in by ``get_registered_funcs`` when entries are omitted, which keeps feature declarations concise but still structured. Developers should treat ``config_table`` as the canonical feature API surface.

Tree Control Flow: Child, Sibling, Loop, Break/Continue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Feature lists are compiled into child/sibling graphs, with tuple-based structures representing loop-like behavior and explicit handling for ``break``/``continue``. Conditional branches are expressed through ``true`` and ``false`` feature entries. This is more expressive than a simple linear list and is central to advanced workflows.

Cleanup and Failure Semantics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Containers maintain cleanup lists and run cleanup handlers on shutdown or unrecoverable exceptions. Data-container behavior distinguishes recoverable one-step node errors from fatal synchronization failures, which is important for avoiding stuck signal/data states. Developers adding complex features should always provide meaningful cleanup handlers for device-safe exits.

Acquisition Mode to Feature-List Mapping
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The model maps acquisition modes (for example ``single``, ``live``, ``z-stack``, ``customized``) to specific feature lists in :file:`src/navigate/model/model.py`. Plugin acquisition modes can register their own feature lists and lifecycle hooks, extending this map without changing core mode logic. This mapping is the first place to inspect when behavior differs by mode.

Dynamic Feature Lists and Shared Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Feature lists can be loaded from strings/files and converted back to string form using helpers in :file:`src/navigate/model/features/feature_related_functions.py`. ``SharedList`` values allow named shared arguments to be preserved and reconstructed across serialization boundaries. Dynamic parameter loaders support late-binding configuration from YAML files.

Hardware and Device Abstractions
--------------------------------

Microscope Composition and Device Startup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Each microscope object is assembled from configuration by :class:`Microscope` in :file:`src/navigate/model/microscope.py`, then connected to started devices from :file:`src/navigate/model/device_startup_functions.py`. The composition layer supports shared physical devices, per-microscope state, and plugin-provided hardware categories. Understanding this assembly path is critical for any new hardware integration work.

Abstract Base Types and Interface Markers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Device and controller layers use abstract contracts and markers, including :class:`DeviceBase` and device-type marker classes in :file:`src/navigate/model/devices/device_types.py`, plus abstract view-controller interfaces in camera view code. Data I/O similarly uses base abstractions like :class:`DataSource` and :class:`DataReader`. These contracts define what new implementations must provide to stay compatible with core orchestration code.

Connection Factories and Reuse Policy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Device startup uses connection factories (serial, integrated, sequence) that cache and reuse device connections, with retry logic via ``auto_redial``. Serial paths are wrapped with performance logging for read/write timing, helping diagnose command latency. This shared-connection strategy reduces duplicate connections and startup instability when multiple devices reference the same hardware endpoint.

Virtual Microscopes and Additional Display Pipes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The model can launch virtual microscopes with synthetic or shared components and independent shared buffers. The controller then creates per-microscope image pipes and camera-view popups to display those streams. This pattern is useful for multi-view workflows and as a template for future multiplexed displays.

Waveform Generation and Waveform UI Updates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Waveform generation combines camera, DAQ, remote-focus, and galvo timing calculations in :class:`Microscope`, then posts ``waveform`` events to the controller. The waveform tab subscribes through the controller event-listener mechanism and redraws plots when these events arrive. Exposure-time adjustments in some modes also feed back into UI state through events.

ASI Model Divergence
^^^^^^^^^^^^^^^^^^^^
:class:`ASIModel` in :file:`src/navigate/model/model.py` overrides key acquisition paths for Tiger-controller workflows, including z-stack position bookkeeping and stack-specific behavior. It preallocates larger position buffers and advances frame indices differently than the default model. Developers working on stack logic should verify both model paths before considering a change complete.

Persistence, Metadata, and Configuration
----------------------------------------

ImageWriter Save Pipeline and Disk-Safety Guards
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:class:`ImageWriter` in :file:`src/navigate/model/features/image_writer.py` is responsible for frame saving, MIP generation, periodic disk-space checks, and acquisition stop signaling on save failures. It also ties saved frames to stage-position metadata via ``data_buffer_positions`` indexing. This class is a high-risk area because save-path bugs can silently corrupt data or metadata alignment.

Data Source and Metadata Abstraction Layer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File formats are implemented behind :class:`DataSource` abstractions (TIFF/OME-TIFF, OME-Zarr, BDV-related paths), while metadata conversion is handled by metadata-source classes. This separation allows format-specific storage logic and shared acquisition metadata logic to evolve independently. New formats should follow this pattern rather than embedding file-format logic directly into acquisition threads.

Controller/Sub-Controller Boundaries and Event Bus
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The main controller owns process orchestration, lifecycle control, and global routing, while sub-controllers own specific UI domains (camera view, histogram, channels, stages, menus, plugins, and more). Sub-controllers publish ``custom_events`` that are registered into the controller’s event-listener map. This keeps feature ownership local while still allowing model events to reach the right UI handlers.

Plugin Loading Architecture (Model and Controller Sides)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Plugin loading is split across model-side and controller-side managers, with support for both filesystem plugins and Python package entry points in :file:`src/navigate/plugins/plugin_manager.py`. Plugins can contribute features, feature lists, acquisition modes, devices, tabs/popups, and custom event handlers. The split design keeps hardware/data extensions near the model and UI extensions near sub-controllers.

Multi-Position Hidden Metadata Columns
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The multi-position controller keeps display columns separate from hidden metadata columns (for example ``X_PIXEL`` and ``Y_PIXEL``) and preserves both through import/export paths. This prevents UI clutter while retaining machine-useful position metadata in YAML/CSV workflows. Any table-schema change should preserve this visible/hidden synchronization behavior.

Configuration Verification and Normalization Pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
At startup, controller code calls verification routines in :file:`src/navigate/config/config.py` to normalize and repair experiment, waveform, and configuration trees. These functions fill defaults, coerce types, prune invalid entries, and synchronize microscope-dependent structures. Treat these functions as the schema safety layer that allows older configs and partial configs to keep running.
