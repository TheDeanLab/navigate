# Navigate Controller Architecture

This directory contains the main application controller for Navigate.

The central class is `Controller` in `controller.py`. It coordinates:

1. The Tkinter GUI
2. The model process (`ObjectInSubprocess`)
3. Sub-controllers for each major UI surface
4. Cross-thread and cross-process event flow

## Big Picture

`Controller` is the orchestration layer in an MVC-style design.

- View:
  - Built from `navigate.view.*`
  - Owned by `self.view`
- Model:
  - Spawned as a subprocess (`Model` or `ASIModel`)
  - Accessed through `self.model`
- Controller:
  - Routes UI commands
  - Receives model events
  - Applies UI updates safely on the Tk main thread

## Key Components

- `controller.py`
  - Main orchestration logic
  - Command router (`execute`)
  - Event pump and Tk thread dispatcher
- `configuration_controller.py`
  - Configuration mutation and validation helpers
- `autofocus_calibration.py`
  - Popup-independent autofocus calibration state and completion handling
- `sub_controllers/`
  - Feature-specific UI controllers (camera, stage, channels, multiposition, etc.)
- `thread_pool.py`
  - Resource-scoped worker thread scheduling (`model`, `camera`, `stop_stage`, ...)

## Startup Flow

When `Controller(...)` is constructed, it performs this sequence:

1. Store the Tk root and install the thread guard (`install_tk_thread_guard`).
2. Create controller queues and the worker-thread pool, then load and validate the
   configuration files.
3. Start the model subprocess and create its image pipe.
4. Apply the GUI theme and construct the main view, autofocus calibration state,
   and UI sub-controllers.
5. Create the main-thread dispatch queue and start the event pump
   (`_schedule_event_pump`).
6. Initialize menus and plugins, then populate experiment settings and camera/MIP
   display state.
7. Dismiss the splash screen, show the main window, and bind resize handling.

## Threading Model (Important)

Tkinter widgets and Tk variables are main-thread-only.

This codebase enforces that with:

- `Controller._run_on_main_thread(...)`
  - Enqueues UI work when called from worker threads
  - Can wait for completion via `wait=True`
- `_main_thread_dispatch_queue`
  - Queue of callables to execute on Tk thread
- `_drain_main_thread_dispatch_queue()`
  - Executes queued UI work
- `_schedule_event_pump()`
  - Repeats every ~20 ms via `root.after(...)`
  - Drains dispatch queue and model events

### Rules for Contributors

- Do not update Tk widgets from worker threads.
- Do not read/write Tk variables from worker threads.
- Do route UI work through `_run_on_main_thread(...)`.
- Use `wait=True` only when the worker depends on completion or ordering.
- Do keep non-UI heavy work in worker threads.

## Event Flow: Model -> GUI

Model events arrive via `self.event_queue`.

`update_event()` runs on the Tk thread and handles events such as:

- `warning`
- `multiposition`
- `update_stage`
- `frame_rate`
- `stop`
- Plugin/listener events from `event_listeners`

Because `update_event()` is called by `_schedule_event_pump()`, UI updates happen on the Tk main thread.

## Command Flow: GUI -> Controller -> Model

UI actions call `Controller.execute(command, *args)`.

`execute(...)` decides whether to:

- Run quickly on the current thread
- Dispatch to worker threads (`self.threads_pool.createThread(...)`)
- Call into model commands (`self.model.run_command(...)`)
- Update local UI state/sub-controller state

This method is the primary command routing layer and extension point for new features.

## Acquisition Path

Acquisition uses both worker threads and Tk-thread marshaling:

1. `execute("acquire" | "autofocus" | etc.)`
2. Worker thread calls `capture_image(...)`
3. UI setup and updates are marshaled using:
   - `_start_capture_ui`
   - `_on_capture_started`
   - `_update_capture_display`
   - `_finish_capture_ui`
4. Image IDs are read from `show_img_pipe` and mapped to `data_buffer`
5. Display/histogram/progress updates happen on the Tk thread

## Plugins and Additional Microscopes

- Plugins can register acquisition modes and event listeners through:
  - `add_acquisition_mode(...)`
  - `register_event_listener(...)`
  - `register_event_listeners(...)`
- Additional microscope windows are launched by:
  - `launch_additional_microscopes(...)`
  - `destroy_virtual_microscope(...)`

Even when images are consumed in worker threads, widget updates are dispatched through `_run_on_main_thread(...)`.

## Safe Extension Checklist

When adding new controller behavior:

1. Add command handling in `execute(...)`.
2. Keep model calls off the Tk thread when they can block.
3. Keep all Tk widget and Tk variable access on Tk thread.
4. If called from a worker, wrap UI calls with `_run_on_main_thread(...)`.
5. Use the existing named thread-pool resources instead of adding ad hoc worker
   or polling threads.
6. Add tests for command routing and thread-safe UI behavior where possible.

## Common Pitfalls

- Direct Tk widget updates from worker threads
  - Can trigger intermittent `TclError` or undefined behavior
- Calling long-running model code on Tk thread
  - Freezes the UI
- Reintroducing ad-hoc event polling threads
  - Bypasses the pump/drain architecture and increases race risk

## Related Files

- `src/navigate/controller/controller.py`
- `src/navigate/controller/thread_pool.py`
- `src/navigate/tools/tk_thread_guard.py`
- `src/navigate/controller/sub_controllers/`
