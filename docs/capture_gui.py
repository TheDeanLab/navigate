#!/usr/bin/env python3

"""Capture navigate GUI screenshots for documentation.

This module uses a capture registry plus CLI selectors so screenshots can be
updated in focused batches or all at once.
"""

import argparse
import json
import math
import os
import sys
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_ROOT = Path(SCRIPT_DIR).parent
SRC_DIR = REPO_ROOT / "src"
DEFAULT_OUTPUT_ROOT = str(Path(SCRIPT_DIR) / "source" / "images")

# Allow running this script directly from the repository checkout without
# requiring an editable install.
if SRC_DIR.exists():
    src_str = str(SRC_DIR)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

from navigate.controller.configurator import Configurator
from navigate.controller.controller import Controller
from navigate.tools.gui import capture_region, tk_window_bbox
from navigate.tools.main_functions import create_parser, evaluate_parser_input_arguments
from navigate.view.splash_screen import SplashScreen


@dataclass(frozen=True)
class CaptureSpec:
    """A single capture definition."""

    name: str
    group: str
    description: str
    context: str
    runner: Callable[[Dict[str, object], argparse.Namespace], str]


def settle_window(root: tk.Tk, passes: int = 3, delay_ms: int = 200) -> None:
    """Allow Tk to finish layout/idle rendering before screenshot capture."""
    try:
        root.deiconify()
        root.lift()
        root.attributes("-topmost", True)
        root.focus_force()
    except tk.TclError:
        pass

    for _ in range(passes):
        root.update_idletasks()
        idle_done = {"value": False}
        root.after_idle(lambda: idle_done.update(value=True))
        while not idle_done["value"]:
            root.update()
        root.after(delay_ms)
        root.update()


MODE_LABELS = {
    "live": "Continuous Scan",
    "z-stack": "Z-Stack",
    "single": "Single Acquisition",
}


def _iter_widgets(widget: tk.Misc) -> Iterable[tk.Misc]:
    yield widget
    try:
        children = widget.winfo_children()
    except tk.TclError:
        return
    for child in children:
        yield from _iter_widgets(child)


def _suppress_hover_tooltips(root: tk.Tk) -> None:
    """Disable transient hover tips to keep screenshots clean and repeatable."""
    for widget in _iter_widgets(root):
        hover = getattr(widget, "hover", None)
        if hover is None:
            continue
        try:
            hover.hidetip()
        except Exception:
            pass
        try:
            hover.update_type("disabled")
        except Exception:
            pass


def _prepare_for_capture(root: tk.Tk, cli_args: argparse.Namespace) -> None:
    """Settle geometry and clear transient hover artifacts before capture."""
    try:
        root.event_generate("<Motion>", warp=True, x=2, y=2)
    except tk.TclError:
        pass
    settle_window(root, passes=cli_args.passes, delay_ms=cli_args.delay_ms)
    _suppress_hover_tooltips(root)
    settle_window(root, passes=1, delay_ms=cli_args.delay_ms)


def _select_settings_tab(ctx: Dict[str, object], tab_attr: str) -> None:
    controller = ctx["controller"]
    tab = getattr(controller.view.settings, tab_attr)
    controller.view.settings.select(tab)


def _set_mode(ctx: Dict[str, object], mode: str) -> None:
    controller = ctx["controller"]
    if mode not in MODE_LABELS:
        raise ValueError(f"Unsupported mode for capture: {mode}")
    controller.acquire_bar_controller.set_mode(mode)
    controller.channels_tab_controller.set_mode("stop")


def _set_idle_acquire_bar(ctx: Dict[str, object]) -> None:
    controller = ctx["controller"]
    acquire_ctrl = controller.acquire_bar_controller
    acquire_bar = acquire_ctrl.view
    acquire_ctrl.is_acquiring = False
    acquire_bar.acquire_btn.configure(text="Acquire", state="normal")
    acquire_bar.pull_down.state(["!disabled", "readonly"])
    acquire_bar.CurAcq.stop()
    acquire_bar.OvrAcq.stop()
    acquire_bar.CurAcq["mode"] = "determinate"
    acquire_bar.OvrAcq["mode"] = "determinate"
    acquire_bar.CurAcq["value"] = 0
    acquire_bar.OvrAcq["value"] = 0
    acquire_bar.total_acquisition_label.config(text="00:00:00")


def _set_mock_live_acquiring(ctx: Dict[str, object]) -> None:
    controller = ctx["controller"]
    acquire_ctrl = controller.acquire_bar_controller
    acquire_bar = acquire_ctrl.view
    _set_mode(ctx, "live")
    acquire_ctrl.is_acquiring = True
    acquire_bar.acquire_btn.configure(text="Stop", state="normal")
    acquire_bar.pull_down.state(["disabled", "readonly"])
    acquire_bar.CurAcq.stop()
    acquire_bar.OvrAcq.stop()
    acquire_bar.CurAcq["mode"] = "determinate"
    acquire_bar.OvrAcq["mode"] = "determinate"
    acquire_bar.CurAcq["value"] = 72
    acquire_bar.OvrAcq["value"] = 38
    acquire_bar.total_acquisition_label.config(text="--:--:--")


def _set_stage_positions(ctx: Dict[str, object], z: float, f: float) -> None:
    controller = ctx["controller"]
    stage_parameters = controller.configuration["experiment"]["StageParameters"]
    stage_parameters["z"] = float(z)
    stage_parameters["f"] = float(f)
    controller.stage_controller.widget_vals["z"].set(float(z))
    controller.stage_controller.widget_vals["f"].set(float(f))


def _dismiss_save_dialog(ctx: Dict[str, object]) -> None:
    controller = ctx["controller"]
    acquire_pop = controller.acquire_bar_controller.acquire_pop
    if acquire_pop is None:
        return
    popup = getattr(acquire_pop, "popup", None)
    if popup is None:
        return
    try:
        popup.dismiss()
    except Exception:
        pass
    controller.acquire_bar_controller.acquire_pop = None


def _open_save_dialog(ctx: Dict[str, object], cli_args: argparse.Namespace):
    controller = ctx["controller"]
    _dismiss_save_dialog(ctx)
    _select_settings_tab(ctx, "channels_tab")
    _set_mode(ctx, "single")
    timepoint = controller.view.settings.channels_tab.stack_timepoint_frame
    timepoint.save_data.set(True)
    controller.acquire_bar_controller.set_save_option(True)
    _prepare_for_capture(ctx["root"], cli_args)
    controller.acquire_bar_controller.launch_popup_window()
    acquire_pop = controller.acquire_bar_controller.acquire_pop
    if acquire_pop is None:
        raise RuntimeError("Failed to open save dialog popup for capture.")
    popup = acquire_pop.popup
    _prepare_for_capture(popup, cli_args)
    return acquire_pop, popup


def _splash_image_path() -> str:
    repo_icon = SRC_DIR / "navigate" / "view" / "icon" / "splash_screen_image.png"
    if repo_icon.exists():
        return str(repo_icon)

    try:
        return str(files("navigate.view.icon").joinpath("splash_screen_image.png"))
    except Exception:
        # Fallback for older repository layouts.
        return os.path.join(
            SCRIPT_DIR,
            "..",
            "navigate",
            "view",
            "icon",
            "splash_screen_image.png",
        )


def _build_controller_context() -> Dict[str, object]:
    root = tk.Tk()
    root.withdraw()
    splash_screen = SplashScreen(root, _splash_image_path())

    config_dir = SRC_DIR / "navigate" / "config"
    parser = create_parser()
    args = parser.parse_args(
        [
            "-sh",
            "--config-file",
            str(config_dir / "configuration.yaml"),
            "--experiment-file",
            str(config_dir / "experiment.yml"),
            "--gui-config-file",
            str(config_dir / "gui_configuration.yml"),
        ]
    )

    (
        configuration_path,
        experiment_path,
        waveform_constants_path,
        rest_api_path,
        waveform_templates_path,
        logging_path,
        configurator,
        gui_configuration_path,
        multi_positions_path,
    ) = evaluate_parser_input_arguments(args)

    controller = Controller(
        root,
        splash_screen,
        configuration_path,
        experiment_path,
        waveform_constants_path,
        rest_api_path,
        waveform_templates_path,
        gui_configuration_path,
        multi_positions_path,
        None,
        args,
    )
    return {"root": root, "controller": controller}


def _build_configurator_context() -> Dict[str, object]:
    root = tk.Tk()
    root.withdraw()
    splash_screen = SplashScreen(root, _splash_image_path())
    configurator = Configurator(root, splash_screen)
    return {"root": root, "configurator": configurator}


def _cleanup_controller_context(ctx: Dict[str, object]) -> None:
    controller = ctx["controller"]
    root = ctx["root"]
    # Best-effort teardown for background model/process threads.
    try:
        if hasattr(controller, "_stop_event_pump"):
            controller._stop_event_pump()
    except Exception:
        pass
    try:
        if getattr(controller, "model", None) is not None:
            controller.model.run_command("terminate")
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass


def _cleanup_configurator_context(ctx: Dict[str, object]) -> None:
    root = ctx["root"]
    try:
        root.destroy()
    except Exception:
        pass


def _capture_widget(widget, out_path: str, pad: int = 0) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bbox = tk_window_bbox(widget, pad=pad)
    capture_region(*bbox, out_path=out_path)
    return out_path


def _capture_bbox(bbox: Tuple[int, int, int, int], out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    capture_region(*bbox, out_path=out_path)
    return out_path


def _bbox_from_path(root: tk.Tk, widget_path: str, pad: int = 0) -> Tuple[int, int, int, int]:
    root.update_idletasks()
    x = int(root.tk.call("winfo", "rootx", widget_path)) - pad
    y = int(root.tk.call("winfo", "rooty", widget_path)) - pad
    w = int(root.tk.call("winfo", "width", widget_path)) + 2 * pad
    h = int(root.tk.call("winfo", "height", widget_path)) + 2 * pad
    return x, y, w, h


def _union_bbox(*bboxes: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
    min_x = min(x for x, _, _, _ in bboxes)
    min_y = min(y for _, y, _, _ in bboxes)
    max_x = max(x + w for x, _, w, _ in bboxes)
    max_y = max(y + h for _, y, _, h in bboxes)
    return min_x, min_y, max_x - min_x, max_y - min_y


def _is_mapped_path(root: tk.Tk, widget_path: str) -> bool:
    try:
        return bool(int(root.tk.call("winfo", "ismapped", widget_path)))
    except tk.TclError:
        return False


def _popup_capture_target(
    cli_args: argparse.Namespace,
    popup_name: str,
    legacy_names: Tuple[str, ...] = (),
) -> Tuple[str, bool]:
    """Resolve popup screenshot output path and legacy skip behavior.

    Returns
    -------
    Tuple[str, bool]
        (path, should_skip_capture)
    """
    out_path = os.path.join(cli_args.output_root, f"popup_{popup_name}.png")
    if os.path.exists(out_path):
        return out_path, True

    for legacy_name in legacy_names:
        legacy_path = os.path.join(cli_args.output_root, legacy_name)
        if os.path.exists(legacy_path):
            return legacy_path, True

    return out_path, False


def _extract_popup_toplevel(popup_obj):
    """Return the top-level widget to capture for a popup object."""
    if isinstance(popup_obj, tk.Toplevel):
        return popup_obj
    popup = getattr(popup_obj, "popup", None)
    if popup is not None:
        return popup
    raise RuntimeError(f"Could not resolve popup toplevel from {type(popup_obj)!r}.")


def _dismiss_popup_obj(popup_obj) -> None:
    """Best-effort close for popup objects and popup toplevels."""
    try:
        popup = _extract_popup_toplevel(popup_obj)
    except Exception:
        return

    try:
        popup.dismiss()
        return
    except Exception:
        pass

    try:
        popup.destroy()
    except Exception:
        pass


def _find_notebook_by_tab_text(root_widget, tab_text: str):
    """Find the first ttk.Notebook containing a tab with matching text."""
    for widget in _iter_widgets(root_widget):
        if isinstance(widget, ttk.Notebook):
            try:
                for tab_id in widget.tabs():
                    if widget.tab(tab_id, "text") == tab_text:
                        return widget
            except tk.TclError:
                continue
    return None


def _select_notebook_tab(root_widget, tab_text: str) -> bool:
    """Select a notebook tab by text if present."""
    notebook = _find_notebook_by_tab_text(root_widget, tab_text)
    if notebook is None:
        return False
    try:
        for tab_id in notebook.tabs():
            if notebook.tab(tab_id, "text") == tab_text:
                notebook.select(tab_id)
                return True
    except tk.TclError:
        return False
    return False


def _capture_popup_obj(
    ctx: Dict[str, object],
    cli_args: argparse.Namespace,
    popup_obj,
    popup_name: str,
    *,
    legacy_names: Tuple[str, ...] = (),
    tab_text: Optional[str] = None,
    pad: int = 2,
) -> str:
    """Capture a popup object to popup_<name>.png with optional legacy-skip."""
    out_path, should_skip = _popup_capture_target(
        cli_args, popup_name, legacy_names=legacy_names
    )
    if should_skip:
        return out_path

    popup = _extract_popup_toplevel(popup_obj)
    try:
        if tab_text:
            _select_notebook_tab(popup, tab_text)
        _prepare_for_capture(popup, cli_args)
        if tab_text:
            _select_notebook_tab(popup, tab_text)
            _prepare_for_capture(popup, cli_args)
        return _capture_widget(popup, out_path, pad=pad)
    finally:
        _dismiss_popup_obj(popup_obj)


def _cleanup_controller_popup_attr(
    controller,
    attr_name: str,
    close_methods: Tuple[str, ...] = ("close_popup", "close_window", "exit_func"),
) -> None:
    """Best-effort teardown for popup controllers stored on the main controller."""
    popup_controller = getattr(controller, attr_name, None)
    if popup_controller is None:
        return

    for method_name in close_methods:
        method = getattr(popup_controller, method_name, None)
        if callable(method):
            try:
                method()
                break
            except Exception:
                pass

    if hasattr(controller, attr_name):
        maybe_controller = getattr(controller, attr_name)
        # If still present, try direct popup dismissal.
        view = getattr(maybe_controller, "view", None)
        if view is not None:
            _dismiss_popup_obj(view)
        popup = getattr(maybe_controller, "popup", None)
        if popup is not None:
            _dismiss_popup_obj(popup)
        if hasattr(controller, attr_name):
            try:
                delattr(controller, attr_name)
            except Exception:
                pass


def _capture_combobox_dropdown(
    root: tk.Tk,
    combobox,
    frame_widget,
    out_path: str,
    cli_args: argparse.Namespace,
    selected_value: str = "",
    pad: int = 2,
) -> str:
    _prepare_for_capture(root, cli_args)
    values = combobox.cget("values")
    if selected_value:
        combobox.set(selected_value)
    elif values:
        combobox.set(values[0])

    popup_path = None
    popup_base = None
    openers = (
        lambda: combobox.event_generate("<Button-1>"),
        lambda: root.tk.call("ttk::combobox::Post", combobox),
    )
    for open_dropdown in openers:
        try:
            combobox.focus_set()
            open_dropdown()
            settle_window(
                root,
                passes=max(3, cli_args.passes),
                delay_ms=cli_args.delay_ms,
            )
            popup_base = str(root.tk.call("ttk::combobox::PopdownWindow", combobox))
        except tk.TclError:
            popup_base = None

        if popup_base is None:
            continue

        # On Tk, the popdown listbox lives under "<popup>.f.l".
        popup_listbox = f"{popup_base}.f.l"
        if _is_mapped_path(root, popup_listbox):
            popup_path = popup_listbox
            break
        if _is_mapped_path(root, popup_base):
            popup_path = popup_base
            break

    frame_bbox = tk_window_bbox(frame_widget, pad=pad)
    if popup_path:
        try:
            popup_bbox = _bbox_from_path(root, popup_path, pad=pad)
            bbox = _union_bbox(frame_bbox, popup_bbox)
        except tk.TclError:
            bbox = frame_bbox
    else:
        bbox = frame_bbox

    captured = _capture_bbox(bbox, out_path)
    try:
        root.tk.call("ttk::combobox::Unpost", combobox)
    except tk.TclError:
        pass
    settle_window(root, passes=1, delay_ms=cli_args.delay_ms)
    return captured


def _capture_main_window(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(
        cli_args.output_root, f"{controller.view.__class__.__name__}.png"
    )
    return _capture_widget(controller.view, out_path)


def _capture_acquire_bar(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "acquire-bar.png")
    return _capture_widget(controller.view.acquire_bar, out_path, pad=2)


def _capture_settings_tab(
    ctx: Dict[str, object], cli_args: argparse.Namespace, attr_name: str
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _select_settings_tab(ctx, attr_name)
    tab = getattr(controller.view.settings, attr_name)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, f"{tab.__class__.__name__}.png")
    return _capture_widget(controller.view.settings, out_path)


def _capture_channel_selector(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    channels_tab = controller.view.settings.channels_tab
    _select_settings_tab(ctx, "channels_tab")
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "channel-selector.png")
    return _capture_widget(channels_tab.channel_widgets_frame, out_path, pad=2)


def _capture_channel_selector_filter_dropdown(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    channels_tab = controller.view.settings.channels_tab
    _select_settings_tab(ctx, "channels_tab")
    _prepare_for_capture(root, cli_args)

    frame = channels_tab.channel_widgets_frame
    if not frame.filterwheel_pulldowns:
        raise RuntimeError("No filter wheel combobox widgets available to capture.")

    filter_combo = frame.filterwheel_pulldowns[0]
    out_path = os.path.join(cli_args.output_root, "channel-selector-filter.png")
    return _capture_combobox_dropdown(
        root=root,
        combobox=filter_combo,
        frame_widget=frame,
        out_path=out_path,
        cli_args=cli_args,
        pad=2,
    )


def _capture_sensor_mode_dropdown(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    camera_settings_tab = controller.view.settings.camera_settings_tab
    _select_settings_tab(ctx, "camera_settings_tab")
    _prepare_for_capture(root, cli_args)

    camera_mode_frame = camera_settings_tab.camera_mode
    sensor_input = camera_mode_frame.inputs["Sensor"]
    sensor_combo = sensor_input.widget
    out_path = os.path.join(cli_args.output_root, "sensor-mode.png")
    return _capture_combobox_dropdown(
        root=root,
        combobox=sensor_combo,
        frame_widget=camera_mode_frame,
        out_path=out_path,
        cli_args=cli_args,
        pad=2,
    )


def _capture_camera_mode_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    camera_settings_tab = controller.view.settings.camera_settings_tab
    _select_settings_tab(ctx, "camera_settings_tab")
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "camera-mode-frame.png")
    return _capture_widget(camera_settings_tab.camera_mode, out_path, pad=2)


def _capture_framerate_info_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    camera_settings_tab = controller.view.settings.camera_settings_tab
    _select_settings_tab(ctx, "camera_settings_tab")
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "framerate-info-frame.png")
    return _capture_widget(camera_settings_tab.framerate_info, out_path, pad=2)


def _capture_region_of_interest_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    camera_settings_tab = controller.view.settings.camera_settings_tab
    _select_settings_tab(ctx, "camera_settings_tab")
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "region-of-interest-frame.png")
    return _capture_widget(camera_settings_tab.camera_roi, out_path, pad=2)


def _prepare_stage_control_capture(
    ctx: Dict[str, object], cli_args: argparse.Namespace
):
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_mode(ctx, "single")
    _select_settings_tab(ctx, "stage_control_tab")
    stage_tab = controller.view.settings.stage_control_tab
    try:
        stage_tab.force_enable_all_axes()
    except Exception:
        pass
    _prepare_for_capture(root, cli_args)
    return stage_tab


def _capture_stage_control_tab_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    stage_tab = _prepare_stage_control_capture(ctx, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-control-tab-frame.png")
    return _capture_widget(stage_tab, out_path, pad=2)


def _capture_stage_positions_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    stage_tab = _prepare_stage_control_capture(ctx, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-positions-frame.png")
    return _capture_widget(stage_tab.position_frame, out_path, pad=2)


def _capture_stage_xy_movement_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    stage_tab = _prepare_stage_control_capture(ctx, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-xy-movement-frame.png")
    return _capture_widget(stage_tab.xy_frame, out_path, pad=2)


def _capture_stage_z_movement_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    stage_tab = _prepare_stage_control_capture(ctx, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-z-movement-frame.png")
    return _capture_widget(stage_tab.z_frame, out_path, pad=2)


def _capture_stage_focus_movement_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    stage_tab = _prepare_stage_control_capture(ctx, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-focus-movement-frame.png")
    return _capture_widget(stage_tab.f_frame, out_path, pad=2)


def _capture_stage_theta_movement_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    stage_tab = _prepare_stage_control_capture(ctx, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-theta-movement-frame.png")
    return _capture_widget(stage_tab.theta_frame, out_path, pad=2)


def _capture_stage_buttons_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    stage_tab = _prepare_stage_control_capture(ctx, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-buttons-frame.png")
    return _capture_widget(stage_tab.stop_frame, out_path, pad=2)


def _capture_roi_definition(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    camera_settings_tab = controller.view.settings.camera_settings_tab
    _select_settings_tab(ctx, "camera_settings_tab")
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "ROI-definition.png")
    return _capture_widget(camera_settings_tab.camera_roi, out_path, pad=2)


def _capture_camera_tab(
    ctx: Dict[str, object], cli_args: argparse.Namespace, attr_name: str
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    tab = getattr(controller.view.camera_waveform, attr_name)
    controller.view.camera_waveform.select(tab)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, f"{tab.__class__.__name__}.png")
    return _capture_widget(controller.view.camera_waveform, out_path)


def _capture_histogram_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    notebook = controller.view.camera_waveform
    camera_tab = notebook.camera_tab
    notebook.select(camera_tab)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "histogram-frame.png")
    return _capture_widget(camera_tab.histogram, out_path, pad=2)


def _capture_intensity_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    notebook = controller.view.camera_waveform
    camera_tab = notebook.camera_tab
    notebook.select(camera_tab)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "intensity-frame.png")
    return _capture_widget(camera_tab.lut, out_path, pad=2)


def _capture_metrics_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    notebook = controller.view.camera_waveform
    camera_tab = notebook.camera_tab
    notebook.select(camera_tab)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "metrics-frame.png")
    return _capture_widget(camera_tab.image_metrics, out_path, pad=2)


def _capture_render_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    notebook = controller.view.camera_waveform
    camera_tab = notebook.camera_tab
    notebook.select(camera_tab)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "render-frame.png")
    return _capture_widget(camera_tab.live_frame, out_path, pad=2)


def _capture_mip_render_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    notebook = controller.view.camera_waveform
    mip_tab = notebook.mip_tab
    notebook.select(mip_tab)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "mip-render-frame.png")
    return _capture_widget(mip_tab.render, out_path, pad=2)


def _populate_waveform_plot_preview(waveform_tab) -> None:
    """Draw representative waveforms for documentation screenshots."""
    fig = waveform_tab.fig
    fig.clear()

    ax_remote_focus = fig.add_subplot(211)
    ax_galvo = fig.add_subplot(212, sharex=ax_remote_focus)

    time_axis = [i * 0.01 for i in range(101)]
    remote_focus = [0.8 * math.sin(2 * math.pi * t * 1.2) for t in time_axis]
    galvo_a = [0.6 * math.sin(2 * math.pi * t * 0.9 + 0.6) for t in time_axis]
    galvo_b = [0.4 * math.sin(2 * math.pi * t * 1.4 - 0.3) for t in time_axis]

    ax_remote_focus.plot(time_axis, remote_focus, color="#1f77b4", linewidth=1.6)
    ax_remote_focus.axvline(x=0.35, color="black", linestyle=":", linewidth=1.0)
    ax_remote_focus.set_ylabel("RF (V)")
    ax_remote_focus.grid(alpha=0.25)

    ax_galvo.plot(time_axis, galvo_a, color="#d62728", linewidth=1.4, label="Galvo 0")
    ax_galvo.plot(time_axis, galvo_b, color="#2ca02c", linewidth=1.4, label="Galvo 1")
    ax_galvo.axvline(x=0.35, color="black", linestyle=":", linewidth=1.0)
    ax_galvo.set_xlabel("Time (ms)")
    ax_galvo.set_ylabel("Galvo (V)")
    ax_galvo.grid(alpha=0.25)
    ax_galvo.legend(loc="upper right", fontsize=7, frameon=False)

    fig.tight_layout()
    waveform_tab.canvas.draw()


def _ensure_waveform_preview_dict(controller) -> None:
    """Provide fallback waveform data for Waveforms tab screenshot capture."""
    waveform_ctrl = getattr(controller, "waveform_tab_controller", None)
    if waveform_ctrl is None:
        return
    if hasattr(waveform_ctrl, "waveform_dict"):
        return

    samples = np.array([i * 0.01 for i in range(101)], dtype=float)
    waveform_ctrl.waveform_dict = {
        "camera_waveform": {
            "CH1": np.array([1 if 0.32 <= t <= 0.38 else 0 for t in samples], dtype=float)
        },
        "remote_focus_waveform": {
            "CH1": np.array(
                [0.8 * math.sin(2 * math.pi * t * 1.2) for t in samples], dtype=float
            )
        },
        "galvo_waveform": [
            {
                "CH1": np.array(
                    [0.6 * math.sin(2 * math.pi * t * 0.9 + 0.6) for t in samples],
                    dtype=float,
                )
            },
            {
                "CH1": np.array(
                    [0.4 * math.sin(2 * math.pi * t * 1.4 - 0.3) for t in samples],
                    dtype=float,
                )
            },
        ],
    }


def _capture_waveform_plots_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    notebook = controller.view.camera_waveform
    waveform_tab = notebook.waveform_tab
    _ensure_waveform_preview_dict(controller)
    notebook.select(waveform_tab)
    _populate_waveform_plot_preview(waveform_tab)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "waveform-plots-frame.png")
    return _capture_widget(waveform_tab.waveform_plots, out_path, pad=2)


def _capture_waveform_settings_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    notebook = controller.view.camera_waveform
    waveform_tab = notebook.waveform_tab
    _ensure_waveform_preview_dict(controller)
    notebook.select(waveform_tab)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "waveform-settings-frame.png")
    return _capture_widget(waveform_tab.waveform_settings, out_path, pad=2)


def _capture_acquire_mode_dropdown(
    ctx: Dict[str, object],
    cli_args: argparse.Namespace,
    mode: str,
    out_name: str,
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _select_settings_tab(ctx, "channels_tab")
    _set_mode(ctx, mode)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, out_name)
    return _capture_combobox_dropdown(
        root=root,
        combobox=controller.view.acquire_bar.pull_down,
        frame_widget=controller.view,
        out_path=out_path,
        cli_args=cli_args,
        selected_value=MODE_LABELS[mode],
        pad=2,
    )


def _capture_continuous_scan_acquire(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _select_settings_tab(ctx, "channels_tab")
    _set_mock_live_acquiring(ctx)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "continuous-scan-acquire.png")
    return _capture_widget(controller.view, out_path)


def _capture_stage_movement_panel(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_mock_live_acquiring(ctx)
    _select_settings_tab(ctx, "stage_control_tab")
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-movement-panel.png")
    return _capture_widget(controller.view, out_path)


def _capture_stop_acquisition(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_mock_live_acquiring(ctx)
    _select_settings_tab(ctx, "channels_tab")
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "stop-acquisition.png")
    return _capture_widget(controller.view, out_path)


def _capture_save_data(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_mode(ctx, "single")
    _select_settings_tab(ctx, "channels_tab")
    channels_tab = controller.view.settings.channels_tab
    channels_tab.stack_timepoint_frame.save_data.set(True)
    controller.acquire_bar_controller.set_save_option(True)
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "save-data.png")
    return _capture_widget(channels_tab.stack_timepoint_frame, out_path, pad=2)


def _capture_multiposition_acquisition_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_mode(ctx, "single")
    _select_settings_tab(ctx, "channels_tab")
    channels_tab = controller.view.settings.channels_tab
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "multiposition-acquisition-frame.png")
    return _capture_widget(channels_tab.multipoint_frame, out_path, pad=2)


def _capture_quick_launch_buttons_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_mode(ctx, "single")
    _select_settings_tab(ctx, "channels_tab")
    channels_tab = controller.view.settings.channels_tab
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "quick-launch-buttons-frame.png")
    return _capture_widget(channels_tab.quick_launch, out_path, pad=2)


def _capture_multiposition_buttons_frame(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_mode(ctx, "single")
    _select_settings_tab(ctx, "multiposition_tab")
    multiposition_tab = controller.view.settings.multiposition_tab
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "multiposition-buttons-frame.png")
    return _capture_widget(multiposition_tab.tiling_buttons, out_path, pad=2)


def _capture_save_dialog_box(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    _, popup = _open_save_dialog(ctx, cli_args)
    out_path = os.path.join(cli_args.output_root, "save-dialog-box.png")
    try:
        return _capture_widget(popup, out_path, pad=2)
    finally:
        _dismiss_save_dialog(ctx)
        _set_idle_acquire_bar(ctx)


def _capture_save_dialog_box_acquire(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    acquire_pop, popup = _open_save_dialog(ctx, cli_args)
    out_path = os.path.join(cli_args.output_root, "save-dialog-box-acquire.png")
    try:
        done_button = acquire_pop.get_buttons()["Done"]
        done_button.focus_set()
        _prepare_for_capture(popup, cli_args)
        return _capture_widget(popup, out_path, pad=2)
    finally:
        _dismiss_save_dialog(ctx)
        _set_idle_acquire_bar(ctx)


def _set_default_z_stack_positions(ctx: Dict[str, object]) -> None:
    controller = ctx["controller"]
    _set_mode(ctx, "z-stack")
    _set_stage_positions(ctx, z=3101.8, f=208.02)
    controller.channels_tab_controller.update_start_position()
    _set_stage_positions(ctx, z=3521.8, f=208.02)
    controller.channels_tab_controller.update_end_position()


def _capture_stage_control_start_pos_zstack(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_mode(ctx, "z-stack")
    _set_stage_positions(ctx, z=3101.8, f=208.02)
    _select_settings_tab(ctx, "stage_control_tab")
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-control-start-pos-zstack.png")
    return _capture_widget(controller.view, out_path)


def _capture_press_start_pos(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_mode(ctx, "z-stack")
    _set_stage_positions(ctx, z=3101.8, f=208.02)
    controller.channels_tab_controller.update_start_position()
    _select_settings_tab(ctx, "channels_tab")
    stack_frame = controller.view.settings.channels_tab.stack_acq_frame
    stack_frame.buttons["set_start"].focus_set()
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "press-start-pos.png")
    return _capture_widget(stack_frame, out_path, pad=2)


def _capture_stage_control_end_pos_zstack(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_default_z_stack_positions(ctx)
    _select_settings_tab(ctx, "stage_control_tab")
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "stage-control-end-pos-zstack.png")
    return _capture_widget(controller.view, out_path)


def _capture_press_end_pos(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_default_z_stack_positions(ctx)
    _select_settings_tab(ctx, "channels_tab")
    stack_frame = controller.view.settings.channels_tab.stack_acq_frame
    stack_frame.buttons["set_end"].focus_set()
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "press-end-pos.png")
    return _capture_widget(stack_frame, out_path, pad=2)


def _capture_define_step_size(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_default_z_stack_positions(ctx)
    _select_settings_tab(ctx, "channels_tab")
    stack_frame = controller.view.settings.channels_tab.stack_acq_frame
    controller.channels_tab_controller.stack_acq_vals["step_size"].set(10.0)
    stack_frame.inputs["step_size"].widget.focus_set()
    _prepare_for_capture(root, cli_args)
    out_path = os.path.join(cli_args.output_root, "define-step-size.png")
    return _capture_widget(stack_frame, out_path, pad=2)


def _capture_laser_cycling_settings(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _set_default_z_stack_positions(ctx)
    _select_settings_tab(ctx, "channels_tab")
    stack_frame = controller.view.settings.channels_tab.stack_acq_frame
    cycling_combo = stack_frame.inputs["cycling"].widget
    out_path = os.path.join(cli_args.output_root, "laser-cycling-settings.png")
    return _capture_combobox_dropdown(
        root=root,
        combobox=cycling_combo,
        frame_widget=stack_frame,
        out_path=out_path,
        cli_args=cli_args,
        selected_value="Per Stack",
        pad=2,
    )


def _capture_continuous_scan_dropdown(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    return _capture_acquire_mode_dropdown(
        ctx,
        cli_args,
        mode="live",
        out_name="continuous-scan-dropdown.png",
    )


def _capture_single_acquisition_dropdown(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    return _capture_acquire_mode_dropdown(
        ctx,
        cli_args,
        mode="single",
        out_name="single-acquisition-dropdown.png",
    )


def _capture_z_stack_acquisition(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    _set_default_z_stack_positions(ctx)
    return _capture_acquire_mode_dropdown(
        ctx,
        cli_args,
        mode="z-stack",
        out_name="z-stack-acquisition.png",
    )


def _capture_configurator(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    root = ctx["root"]
    settle_window(root, passes=max(5, cli_args.passes), delay_ms=cli_args.delay_ms)
    out_path = os.path.join(cli_args.output_root, "configurator.PNG")
    return _capture_widget(root, out_path)


SMART_ROUTINE_CONTENT_BASE = '[{"name": PrepareNextChannel}]'
SMART_ROUTINE_CONTENT_DOUBLE_PREP = (
    '[{"name": PrepareNextChannel}, {"name": PrepareNextChannel}]'
)
SMART_ROUTINE_CONTENT_MOVE_NEXT = (
    '[{"name": PrepareNextChannel}, {"name": MoveToNextPositionInMultiPositionTable}]'
)
SMART_ROUTINE_CONTENT_DETECT = (
    '[{"name": PrepareNextChannel}, {"name": MoveToNextPositionInMultiPositionTable}, '
    '{"name": DetectTissueInStackAndReturn}]'
)
SMART_ROUTINE_CONTENT_LOOP = (
    '[{"name": PrepareNextChannel}, {"name": MoveToNextPositionInMultiPositionTable}, '
    '{"name": DetectTissueInStackAndReturn}, {"name": LoopByCount}]'
)
SMART_ROUTINE_CONTENT_LOOP_GROUPED = (
    '[{"name": PrepareNextChannel}, ({"name": MoveToNextPositionInMultiPositionTable}, '
    '{"name": DetectTissueInStackAndReturn}, {"name": LoopByCount})]'
)
SMART_ROUTINE_CONTENT_DECISION = (
    '[{"name": PrepareNextChannel}, ({"name": MoveToNextPositionInMultiPositionTable}, '
    '{"name": DetectTissueInStackAndReturn, "args": (1, 0.5, None), '
    '"true": [{"name": ZStackAcquisition, "args": (False, False, "z-stack")}], '
    '"false": "continue"}, {"name": LoopByCount})]'
)


def _close_feature_list_popup(ctx: Dict[str, object]) -> None:
    controller = ctx["controller"]
    popup_controller = getattr(controller, "features_popup_controller", None)
    if popup_controller is None:
        return
    try:
        popup_controller.exit_func()
    except Exception:
        try:
            popup_controller.view.popup.dismiss()
        except Exception:
            pass
    finally:
        if hasattr(controller, "features_popup_controller"):
            try:
                delattr(controller, "features_popup_controller")
            except Exception:
                pass


def _open_feature_list_popup(
    ctx: Dict[str, object],
    cli_args: argparse.Namespace,
    content: str,
    feature_list_name: str = "TestFeature",
):
    controller = ctx["controller"]
    _set_idle_acquire_bar(ctx)
    _select_settings_tab(ctx, "channels_tab")
    _close_feature_list_popup(ctx)
    controller.menu_controller.popup_feature_list_setting()
    popup_controller = controller.features_popup_controller
    popup_view = popup_controller.view
    popup_view.inputs["feature_list_name"].set(feature_list_name)
    popup_view.inputs["content"].delete("1.0", tk.END)
    popup_view.inputs["content"].insert("1.0", content)
    popup_controller.feature_list_graph_controller.draw_feature_list_graph(
        new_list_flag=True
    )
    _prepare_for_capture(popup_view.popup, cli_args)
    return popup_controller


def _capture_feature_list_popup_state(
    ctx: Dict[str, object],
    cli_args: argparse.Namespace,
    *,
    content: str,
    out_name: str,
) -> str:
    popup_controller = _open_feature_list_popup(ctx, cli_args, content=content)
    out_path = os.path.join(cli_args.output_root, out_name)
    try:
        _prepare_for_capture(popup_controller.view.popup, cli_args)
        return _capture_widget(popup_controller.view.popup, out_path, pad=2)
    finally:
        _close_feature_list_popup(ctx)


def _capture_feature_gui_1(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    return _capture_feature_list_popup_state(
        ctx,
        cli_args,
        content=SMART_ROUTINE_CONTENT_BASE,
        out_name="feature_gui_1.png",
    )


def _capture_feature_gui_2(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    popup_controller = _open_feature_list_popup(
        ctx, cli_args, content=SMART_ROUTINE_CONTENT_BASE
    )
    out_path = os.path.join(cli_args.output_root, "feature_gui_2.png")
    context_menu = None
    try:
        feature_graph = popup_controller.feature_list_graph_controller
        feature_buttons = feature_graph.feature_list_view.winfo_children()
        if not feature_buttons:
            raise RuntimeError("Feature list graph did not render any nodes.")
        anchor = feature_buttons[0]
        context_menu = tk.Menu(feature_graph.feature_list_view, tearoff=0)
        context_menu.add_command(label="Delete")
        context_menu.add_command(label="Insert Before")
        context_menu.add_command(label="Insert After")
        _prepare_for_capture(popup_controller.view.popup, cli_args)
        context_menu.post(
            anchor.winfo_rootx() + 8, anchor.winfo_rooty() + anchor.winfo_height() + 6
        )
        settle_window(
            popup_controller.view.popup,
            passes=max(2, cli_args.passes),
            delay_ms=cli_args.delay_ms,
        )
        return _capture_widget(popup_controller.view.popup, out_path, pad=2)
    finally:
        if context_menu is not None:
            try:
                context_menu.unpost()
                context_menu.destroy()
            except Exception:
                pass
        _close_feature_list_popup(ctx)


def _capture_feature_gui_3(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    return _capture_feature_list_popup_state(
        ctx,
        cli_args,
        content=SMART_ROUTINE_CONTENT_DOUBLE_PREP,
        out_name="feature_gui_3.png",
    )


def _capture_feature_gui_4(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    popup_controller = _open_feature_list_popup(
        ctx, cli_args, content=SMART_ROUTINE_CONTENT_DOUBLE_PREP
    )
    out_path = os.path.join(cli_args.output_root, "feature_gui_4.png")
    try:
        feature_graph = popup_controller.feature_list_graph_controller
        feature_graph.show_config_popup(1)(None)
        if not feature_graph.child_popups:
            raise RuntimeError("Failed to open feature configuration popup.")
        config_popup = feature_graph.child_popups[-1]
        config_popup.feature_name_widget.set("MoveToNextPositionInMultiPositionTable")
        config_popup.feature_name_widget.widget.event_generate("<<ComboboxSelected>>")
        _prepare_for_capture(config_popup.popup, cli_args)
        return _capture_widget(config_popup.popup, out_path, pad=2)
    finally:
        try:
            popup_controller.close_child_popups()
        except Exception:
            pass
        _close_feature_list_popup(ctx)


def _capture_feature_gui_5(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    return _capture_feature_list_popup_state(
        ctx,
        cli_args,
        content=SMART_ROUTINE_CONTENT_MOVE_NEXT,
        out_name="feature_gui_5.png",
    )


def _capture_feature_gui_6(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    return _capture_feature_list_popup_state(
        ctx,
        cli_args,
        content=SMART_ROUTINE_CONTENT_DETECT,
        out_name="feature_gui_6.png",
    )


def _capture_feature_gui_7(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    return _capture_feature_list_popup_state(
        ctx,
        cli_args,
        content=SMART_ROUTINE_CONTENT_LOOP,
        out_name="feature_gui_7.png",
    )


def _capture_feature_gui_8(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    return _capture_feature_list_popup_state(
        ctx,
        cli_args,
        content=SMART_ROUTINE_CONTENT_LOOP_GROUPED,
        out_name="feature_gui_8.png",
    )


def _capture_feature_gui_9(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    return _capture_feature_list_popup_state(
        ctx,
        cli_args,
        content=SMART_ROUTINE_CONTENT_DECISION,
        out_name="feature_gui_9.png",
    )


def _capture_feature_gui_10(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    popup_controller = _open_feature_list_popup(
        ctx, cli_args, content=SMART_ROUTINE_CONTENT_DECISION
    )
    out_path = os.path.join(cli_args.output_root, "feature_gui_10.png")
    try:
        feature_graph = popup_controller.feature_list_graph_controller
        feature_graph.show_config_popup(2)(None)
        if not feature_graph.child_popups:
            raise RuntimeError("Failed to open decision-node configuration popup.")
        config_popup = feature_graph.child_popups[-1]
        _prepare_for_capture(config_popup.popup, cli_args)
        return _capture_widget(config_popup.popup, out_path, pad=2)
    finally:
        try:
            popup_controller.close_child_popups()
        except Exception:
            pass
        _close_feature_list_popup(ctx)


def _set_example_multiposition_table(ctx: Dict[str, object]) -> None:
    controller = ctx["controller"]
    stage_axes = controller.configuration_controller.stage_axes
    row_1 = {
        "x": -2400.0,
        "y": -13000.0,
        "z": 4845.4,
        "theta": 208.02,
        "f": -27016.0,
    }
    row_2 = {
        "x": 1584.7,
        "y": -13000.0,
        "z": 4845.4,
        "theta": 208.02,
        "f": -27016.0,
    }
    headers = [axis.upper() for axis in stage_axes]
    positions = [
        headers,
        [row_1.get(axis.lower(), 0.0) for axis in stage_axes],
        [row_2.get(axis.lower(), 0.0) for axis in stage_axes],
    ]
    controller.multiposition_tab_controller.set_positions(positions)


def _select_multiposition_row(ctx: Dict[str, object], row_index: int) -> None:
    table = ctx["controller"].multiposition_tab_controller.table
    max_row = max(0, table.model.df.shape[0] - 1)
    selected = min(max(row_index, 0), max_row)
    table.currentrow = selected
    try:
        table.setSelectedRow(selected)
    except Exception:
        pass
    try:
        table.redraw()
        table.tableChanged()
    except Exception:
        pass


def _capture_multiposition_example(
    ctx: Dict[str, object],
    cli_args: argparse.Namespace,
    *,
    out_name: str,
    row_index: int,
) -> str:
    controller = ctx["controller"]
    _set_mock_live_acquiring(ctx)
    _select_settings_tab(ctx, "multiposition_tab")
    _set_example_multiposition_table(ctx)
    _select_multiposition_row(ctx, row_index)
    _prepare_for_capture(ctx["root"], cli_args)
    out_path = os.path.join(cli_args.output_root, out_name)
    return _capture_widget(controller.view, out_path)


def _capture_multiposition_tissue(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    return _capture_multiposition_example(
        ctx,
        cli_args,
        out_name="multiposition_tissue.png",
        row_index=0,
    )


def _capture_multiposition_empty(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    return _capture_multiposition_example(
        ctx,
        cli_args,
        out_name="multiposition_empty.png",
        row_index=1,
    )


def _capture_popup_save_dialog_misc_notes(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    out_path, should_skip = _popup_capture_target(
        cli_args,
        "save_dialog_misc_notes",
        legacy_names=("save-dialog-box.png",),
    )
    if should_skip:
        return out_path

    _, popup = _open_save_dialog(ctx, cli_args)
    try:
        _select_notebook_tab(popup, "Misc. Notes")
        _prepare_for_capture(popup, cli_args)
        return _capture_widget(popup, out_path, pad=2)
    finally:
        _dismiss_save_dialog(ctx)
        _set_idle_acquire_bar(ctx)


def _capture_popup_save_dialog_bdv_settings(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    out_path, should_skip = _popup_capture_target(
        cli_args, "save_dialog_bdv_settings"
    )
    if should_skip:
        return out_path

    _, popup = _open_save_dialog(ctx, cli_args)
    try:
        _select_notebook_tab(popup, "BDV Settings")
        _prepare_for_capture(popup, cli_args)
        return _capture_widget(popup, out_path, pad=2)
    finally:
        _dismiss_save_dialog(ctx)
        _set_idle_acquire_bar(ctx)


def _capture_popup_autofocus(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    controller = ctx["controller"]
    out_path, should_skip = _popup_capture_target(cli_args, "autofocus_settings")
    if should_skip:
        return out_path

    _cleanup_controller_popup_attr(controller, "af_popup_controller")
    controller.menu_controller.popup_autofocus_setting()
    popup_controller = controller.af_popup_controller
    popup_controller.widgets["calibration_action"].set("Auto Defocus")
    popup = popup_controller.view.popup

    try:
        _prepare_for_capture(popup, cli_args)
        return _capture_widget(popup, out_path, pad=2)
    finally:
        _cleanup_controller_popup_attr(controller, "af_popup_controller")


def _capture_popup_camera_map_settings(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.camera_map_setting_popup import CameraMapSettingPopup

    popup_obj = CameraMapSettingPopup(ctx["controller"].view)
    return _capture_popup_obj(ctx, cli_args, popup_obj, "camera_map_settings")


def _capture_popup_advanced_camera_settings(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.camera_setting_popup import AdvancedCameraSettingPopup

    popup_obj = AdvancedCameraSettingPopup(ctx["controller"].view)
    popup_obj.populate_view({"x": False, "y": False})
    return _capture_popup_obj(ctx, cli_args, popup_obj, "advanced_camera_settings")


def _capture_popup_camera_settings(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.camera_setting_popup import CameraSettingPopup

    microscope_name = ctx["controller"].configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    popup_obj = CameraSettingPopup(ctx["controller"].view, microscope_name)
    return _capture_popup_obj(ctx, cli_args, popup_obj, "camera_settings")


def _capture_popup_additional_camera_view(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.camera_view_popup_window import CameraViewPopupWindow

    microscope_name = ctx["controller"].configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    popup_obj = CameraViewPopupWindow(ctx["controller"].view, microscope_name)
    return _capture_popup_obj(ctx, cli_args, popup_obj, "additional_camera_view")


def _capture_popup_performance_diagnostics(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.diagnostics_popup import DiagnosticsPopup

    popup_obj = DiagnosticsPopup(ctx["controller"].view)
    return _capture_popup_obj(
        ctx,
        cli_args,
        popup_obj,
        "performance_diagnostics",
    )


def _capture_popup_feature_list(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.feature_list_popup import FeatureListPopup

    popup_obj = FeatureListPopup(ctx["controller"].view, title="Add New Feature List")
    popup_obj.inputs["feature_list_name"].set("Example Feature List")
    popup_obj.inputs["content"].insert("1.0", SMART_ROUTINE_CONTENT_BASE)
    return _capture_popup_obj(ctx, cli_args, popup_obj, "feature_list")


def _capture_popup_feature_config(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.feature_list_popup import FeatureConfigPopup

    popup_obj = FeatureConfigPopup(
        ctx["controller"].view,
        title="Feature Configuration",
        features=["PrepareNextChannel", "LoopByCount", "ZStackAcquisition"],
        feature_name="LoopByCount",
        args_name=["channels", "continue_flag"],
        args_value=["(channels,)", True],
    )
    return _capture_popup_obj(ctx, cli_args, popup_obj, "feature_config")


def _capture_popup_feature_advanced_settings(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.feature_list_popup import FeatureAdvancedSettingPopup

    popup_obj = FeatureAdvancedSettingPopup(
        ctx["controller"].view,
        title="Advanced Setting",
        features=["PrepareNextChannel", "LoopByCount", "DetectTissueInStackAndReturn"],
        feature_name="LoopByCount",
    )
    popup_obj.build_widgets(
        args_name=["callbacks", "conditions"],
        parameter_config={
            "callbacks": {"example_callback": "None"},
            "conditions": {"example_condition": "None"},
        },
    )
    return _capture_popup_obj(ctx, cli_args, popup_obj, "feature_advanced_settings")


def _capture_popup_ilastik_settings(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.ilastik_setting_popup import ilastik_setting_popup

    popup_obj = ilastik_setting_popup(ctx["controller"].view)
    return _capture_popup_obj(ctx, cli_args, popup_obj, "ilastik_settings")


def _capture_popup_configure_microscopes(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.microscope_setting_popup_window import (
        MicroscopeSettingPopupWindow,
    )

    microscope_info = ctx["controller"].model.get_microscope_info()
    popup_obj = MicroscopeSettingPopupWindow(ctx["controller"].view, microscope_info)
    return _capture_popup_obj(ctx, cli_args, popup_obj, "configure_microscopes")


def _capture_popup_plugins(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.plugins_popup import PluginsPopup

    popup_obj = PluginsPopup(ctx["controller"].view)
    popup_obj.build_widgets(
        {
            "Example Plugin": "/path/to/example/plugin",
            "Calibration Plugin": "/path/to/calibration/plugin",
        }
    )
    return _capture_popup_obj(ctx, cli_args, popup_obj, "plugins")


def _capture_popup_stage_advanced_parameters(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.stages_advanced_popup import AdvancedStageParametersPopup

    controller = ctx["controller"]
    microscope_name = controller.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]
    stage_axes = [axis for axis in controller.configuration_controller.stage_axes]
    stage_cfg = controller.configuration["configuration"]["microscopes"][
        microscope_name
    ]["stage"]

    min_dict = {axis: stage_cfg.get(f"{axis}_min", -10000.0) for axis in stage_axes}
    max_dict = {axis: stage_cfg.get(f"{axis}_max", 10000.0) for axis in stage_axes}
    flip_axes = {axis: stage_cfg.get(f"flip_{axis}", False) for axis in stage_axes}
    offsets = {axis: stage_cfg.get(f"{axis}_offset", 0.0) for axis in stage_axes}
    home_dict = {axis: stage_cfg.get(f"{axis}_home", 0.0) for axis in stage_axes}

    popup_obj = AdvancedStageParametersPopup(controller.view)
    popup_obj.populate_view(
        stages=stage_axes,
        min_dict=min_dict,
        max_dict=max_dict,
        flip_axes=flip_axes,
        offsets=offsets,
        home_dict=home_dict,
    )
    return _capture_popup_obj(ctx, cli_args, popup_obj, "advanced_stage_parameters")


def _capture_popup_tiling_wizard(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.tiling_wizard_popup import TilingWizardPopup

    axes = [axis.upper() for axis in ctx["controller"].configuration_controller.stage_axes]
    popup_obj = TilingWizardPopup(ctx["controller"].view, axes=axes)
    return _capture_popup_obj(ctx, cli_args, popup_obj, "tiling_wizard")


def _capture_popup_waveform_parameters(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.waveform_parameter_popup_window import (
        WaveformParameterPopupWindow,
    )

    popup_obj = WaveformParameterPopupWindow(
        ctx["controller"].view, ctx["controller"].configuration_controller
    )
    return _capture_popup_obj(ctx, cli_args, popup_obj, "waveform_parameters")


def _build_advanced_waveform_popup(ctx: Dict[str, object]):
    from navigate.view.popups.waveform_parameter_popup_window import (
        AdvancedWaveformParameterPopupWindow,
    )

    popup_obj = AdvancedWaveformParameterPopupWindow(ctx["controller"].view)
    popup_obj.generate_parameter_frame(
        factors=["Channel 1", "Channel 2"],
        galvos=[
            [(0.10, 0.00), (0.12, 0.02)],
            [(0.08, 0.01), (0.09, 0.02)],
            [(0.06, 0.01), (0.07, 0.03)],
        ],
    )
    return popup_obj


def _capture_popup_advanced_waveform_channel_1(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    popup_obj = _build_advanced_waveform_popup(ctx)
    return _capture_popup_obj(
        ctx,
        cli_args,
        popup_obj,
        "advanced_waveform_channel_1",
        tab_text="Channel 1",
    )


def _capture_popup_advanced_waveform_channel_2(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    popup_obj = _build_advanced_waveform_popup(ctx)
    return _capture_popup_obj(
        ctx,
        cli_args,
        popup_obj,
        "advanced_waveform_channel_2",
        tab_text="Channel 2",
    )


def _capture_popup_adaptive_optics_tony_wilson(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.adaptiveoptics_popup import AdaptiveOpticsPopup

    popup_obj = AdaptiveOpticsPopup(ctx["controller"].view)
    return _capture_popup_obj(
        ctx,
        cli_args,
        popup_obj,
        "adaptive_optics_tony_wilson",
        tab_text="Tony Wilson",
    )


def _capture_popup_adaptive_optics_cnn_ao(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    from navigate.view.popups.adaptiveoptics_popup import AdaptiveOpticsPopup

    popup_obj = AdaptiveOpticsPopup(ctx["controller"].view)
    return _capture_popup_obj(
        ctx,
        cli_args,
        popup_obj,
        "adaptive_optics_cnn_ao",
        tab_text="CNN-AO",
    )


CAPTURES: List[CaptureSpec] = [
    CaptureSpec(
        name="main-window",
        group="main-ui",
        description="Main navigate application window",
        context="controller",
        runner=_capture_main_window,
    ),
    CaptureSpec(
        name="acquire-bar",
        group="main-ui",
        description="Acquire bar frame at the top of the main window",
        context="controller",
        runner=_capture_acquire_bar,
    ),
    CaptureSpec(
        name="settings-camera",
        group="main-ui",
        description="Camera settings notebook tab",
        context="controller",
        runner=lambda ctx, args: _capture_settings_tab(ctx, args, "camera_settings_tab"),
    ),
    CaptureSpec(
        name="sensor-mode",
        group="main-ui",
        description="Camera Mode frame with Sensor combobox dropdown opened",
        context="controller",
        runner=_capture_sensor_mode_dropdown,
    ),
    CaptureSpec(
        name="camera-mode-frame",
        group="main-ui",
        description="Camera Mode labelframe in Camera Settings tab",
        context="controller",
        runner=_capture_camera_mode_frame,
    ),
    CaptureSpec(
        name="framerate-info-frame",
        group="main-ui",
        description="Framerate Info labelframe in Camera Settings tab",
        context="controller",
        runner=_capture_framerate_info_frame,
    ),
    CaptureSpec(
        name="region-of-interest-frame",
        group="main-ui",
        description="Region of Interest Settings frame in Camera Settings tab",
        context="controller",
        runner=_capture_region_of_interest_frame,
    ),
    CaptureSpec(
        name="roi-definition",
        group="main-ui",
        description="Region of Interest Settings frame in Camera Settings",
        context="controller",
        runner=_capture_roi_definition,
    ),
    CaptureSpec(
        name="settings-channels",
        group="main-ui",
        description="Channels settings notebook tab",
        context="controller",
        runner=lambda ctx, args: _capture_settings_tab(ctx, args, "channels_tab"),
    ),
    CaptureSpec(
        name="channel-selector",
        group="main-ui",
        description="ChannelCreator frame used in getting-started docs",
        context="controller",
        runner=_capture_channel_selector,
    ),
    CaptureSpec(
        name="channel-selector-filter",
        group="main-ui",
        description="ChannelCreator frame with filter combobox dropdown opened",
        context="controller",
        runner=_capture_channel_selector_filter_dropdown,
    ),
    CaptureSpec(
        name="multiposition-acquisition-frame",
        group="main-ui",
        description="Multi-Position Acquisition labelframe in Channels tab",
        context="controller",
        runner=_capture_multiposition_acquisition_frame,
    ),
    CaptureSpec(
        name="quick-launch-buttons-frame",
        group="main-ui",
        description="Quick Launch Buttons labelframe in Channels tab",
        context="controller",
        runner=_capture_quick_launch_buttons_frame,
    ),
    CaptureSpec(
        name="settings-stage-control",
        group="main-ui",
        description="Stage control settings notebook tab",
        context="controller",
        runner=lambda ctx, args: _capture_settings_tab(ctx, args, "stage_control_tab"),
    ),
    CaptureSpec(
        name="stage-control-tab-frame",
        group="main-ui",
        description="Stage Control tab frame",
        context="controller",
        runner=_capture_stage_control_tab_frame,
    ),
    CaptureSpec(
        name="stage-positions-frame",
        group="main-ui",
        description="Stage Positions frame in Stage Control tab",
        context="controller",
        runner=_capture_stage_positions_frame,
    ),
    CaptureSpec(
        name="stage-xy-movement-frame",
        group="main-ui",
        description="XY Movement frame in Stage Control tab",
        context="controller",
        runner=_capture_stage_xy_movement_frame,
    ),
    CaptureSpec(
        name="stage-z-movement-frame",
        group="main-ui",
        description="Z Movement frame in Stage Control tab",
        context="controller",
        runner=_capture_stage_z_movement_frame,
    ),
    CaptureSpec(
        name="stage-focus-movement-frame",
        group="main-ui",
        description="Focus Movement frame in Stage Control tab",
        context="controller",
        runner=_capture_stage_focus_movement_frame,
    ),
    CaptureSpec(
        name="stage-theta-movement-frame",
        group="main-ui",
        description="Theta Movement frame in Stage Control tab",
        context="controller",
        runner=_capture_stage_theta_movement_frame,
    ),
    CaptureSpec(
        name="stage-buttons-frame",
        group="main-ui",
        description="Stage movement interrupt and joystick buttons frame",
        context="controller",
        runner=_capture_stage_buttons_frame,
    ),
    CaptureSpec(
        name="settings-multiposition",
        group="main-ui",
        description="Multiposition settings notebook tab",
        context="controller",
        runner=lambda ctx, args: _capture_settings_tab(ctx, args, "multiposition_tab"),
    ),
    CaptureSpec(
        name="multiposition-buttons-frame",
        group="main-ui",
        description="Multi-Position buttons frame in Multi-Position tab",
        context="controller",
        runner=_capture_multiposition_buttons_frame,
    ),
    CaptureSpec(
        name="camera-tab",
        group="main-ui",
        description="Camera display tab",
        context="controller",
        runner=lambda ctx, args: _capture_camera_tab(ctx, args, "camera_tab"),
    ),
    CaptureSpec(
        name="histogram-frame",
        group="main-ui",
        description="HistogramFrame in Camera display tab",
        context="controller",
        runner=_capture_histogram_frame,
    ),
    CaptureSpec(
        name="intensity-frame",
        group="main-ui",
        description="IntensityFrame in Camera display tab",
        context="controller",
        runner=_capture_intensity_frame,
    ),
    CaptureSpec(
        name="metrics-frame",
        group="main-ui",
        description="MetricsFrame in Camera display tab",
        context="controller",
        runner=_capture_metrics_frame,
    ),
    CaptureSpec(
        name="render-frame",
        group="main-ui",
        description="RenderFrame in Camera display tab",
        context="controller",
        runner=_capture_render_frame,
    ),
    CaptureSpec(
        name="mip-render-frame",
        group="main-ui",
        description="MipRenderFrame in MIP display tab",
        context="controller",
        runner=_capture_mip_render_frame,
    ),
    CaptureSpec(
        name="waveform-plots-frame",
        group="main-ui",
        description="Waveform plots frame in Waveform tab",
        context="controller",
        runner=_capture_waveform_plots_frame,
    ),
    CaptureSpec(
        name="waveform-settings-frame",
        group="main-ui",
        description="WaveformSettingsFrame in Waveform tab",
        context="controller",
        runner=_capture_waveform_settings_frame,
    ),
    CaptureSpec(
        name="mip-tab",
        group="main-ui",
        description="MIP display tab",
        context="controller",
        runner=lambda ctx, args: _capture_camera_tab(ctx, args, "mip_tab"),
    ),
    CaptureSpec(
        name="continuous-scan-dropdown",
        group="acquiring-data",
        description="Acquire mode dropdown opened on Continuous Scan",
        context="controller",
        runner=_capture_continuous_scan_dropdown,
    ),
    CaptureSpec(
        name="continuous-scan-acquire",
        group="acquiring-data",
        description="Main window in mock continuous acquisition state",
        context="controller",
        runner=_capture_continuous_scan_acquire,
    ),
    CaptureSpec(
        name="stage-movement-panel",
        group="acquiring-data",
        description="Stage control panel during mock continuous acquisition",
        context="controller",
        runner=_capture_stage_movement_panel,
    ),
    CaptureSpec(
        name="stop-acquisition",
        group="acquiring-data",
        description="Acquire bar in stop-enabled state",
        context="controller",
        runner=_capture_stop_acquisition,
    ),
    CaptureSpec(
        name="save-data",
        group="acquiring-data",
        description="Timepoint settings frame with Save Data enabled",
        context="controller",
        runner=_capture_save_data,
    ),
    CaptureSpec(
        name="single-acquisition-dropdown",
        group="acquiring-data",
        description="Acquire mode dropdown opened on Single Acquisition",
        context="controller",
        runner=_capture_single_acquisition_dropdown,
    ),
    CaptureSpec(
        name="save-dialog-box",
        group="acquiring-data",
        description="File Saving Dialog popup",
        context="controller",
        runner=_capture_save_dialog_box,
    ),
    CaptureSpec(
        name="save-dialog-box-acquire",
        group="acquiring-data",
        description="File Saving Dialog popup with Acquire Data button focused",
        context="controller",
        runner=_capture_save_dialog_box_acquire,
    ),
    CaptureSpec(
        name="popup-save-dialog-misc-notes",
        group="popups",
        description="Save dialog popup with Misc. Notes tab",
        context="controller",
        runner=_capture_popup_save_dialog_misc_notes,
    ),
    CaptureSpec(
        name="popup-save-dialog-bdv-settings",
        group="popups",
        description="Save dialog popup with BDV Settings tab",
        context="controller",
        runner=_capture_popup_save_dialog_bdv_settings,
    ),
    CaptureSpec(
        name="popup-autofocus-settings",
        group="popups",
        description="Autofocus settings popup",
        context="controller",
        runner=_capture_popup_autofocus,
    ),
    CaptureSpec(
        name="popup-camera-map-settings",
        group="popups",
        description="Camera map settings popup",
        context="controller",
        runner=_capture_popup_camera_map_settings,
    ),
    CaptureSpec(
        name="popup-camera-settings",
        group="popups",
        description="Camera settings popup window",
        context="controller",
        runner=_capture_popup_camera_settings,
    ),
    CaptureSpec(
        name="popup-advanced-camera-settings",
        group="popups",
        description="Advanced camera settings popup",
        context="controller",
        runner=_capture_popup_advanced_camera_settings,
    ),
    CaptureSpec(
        name="popup-additional-camera-view",
        group="popups",
        description="Additional camera view popup window",
        context="controller",
        runner=_capture_popup_additional_camera_view,
    ),
    CaptureSpec(
        name="popup-performance-diagnostics",
        group="popups",
        description="Performance diagnostics popup",
        context="controller",
        runner=_capture_popup_performance_diagnostics,
    ),
    CaptureSpec(
        name="popup-feature-list",
        group="popups",
        description="Feature list popup",
        context="controller",
        runner=_capture_popup_feature_list,
    ),
    CaptureSpec(
        name="popup-feature-config",
        group="popups",
        description="Feature configuration popup",
        context="controller",
        runner=_capture_popup_feature_config,
    ),
    CaptureSpec(
        name="popup-feature-advanced-settings",
        group="popups",
        description="Feature advanced settings popup",
        context="controller",
        runner=_capture_popup_feature_advanced_settings,
    ),
    CaptureSpec(
        name="popup-ilastik-settings",
        group="popups",
        description="Ilastik settings popup",
        context="controller",
        runner=_capture_popup_ilastik_settings,
    ),
    CaptureSpec(
        name="popup-configure-microscopes",
        group="popups",
        description="Configure microscopes popup",
        context="controller",
        runner=_capture_popup_configure_microscopes,
    ),
    CaptureSpec(
        name="popup-plugins",
        group="popups",
        description="Plugins popup window",
        context="controller",
        runner=_capture_popup_plugins,
    ),
    CaptureSpec(
        name="popup-advanced-stage-parameters",
        group="popups",
        description="Advanced stage parameters popup",
        context="controller",
        runner=_capture_popup_stage_advanced_parameters,
    ),
    CaptureSpec(
        name="popup-tiling-wizard",
        group="popups",
        description="Tiling wizard popup",
        context="controller",
        runner=_capture_popup_tiling_wizard,
    ),
    CaptureSpec(
        name="popup-waveform-parameters",
        group="popups",
        description="Waveform parameter settings popup",
        context="controller",
        runner=_capture_popup_waveform_parameters,
    ),
    CaptureSpec(
        name="popup-advanced-waveform-channel-1",
        group="popups",
        description="Advanced waveform popup, Channel 1 tab",
        context="controller",
        runner=_capture_popup_advanced_waveform_channel_1,
    ),
    CaptureSpec(
        name="popup-advanced-waveform-channel-2",
        group="popups",
        description="Advanced waveform popup, Channel 2 tab",
        context="controller",
        runner=_capture_popup_advanced_waveform_channel_2,
    ),
    CaptureSpec(
        name="popup-adaptive-optics-tony-wilson",
        group="popups",
        description="Adaptive optics popup, Tony Wilson tab",
        context="controller",
        runner=_capture_popup_adaptive_optics_tony_wilson,
    ),
    CaptureSpec(
        name="popup-adaptive-optics-cnn-ao",
        group="popups",
        description="Adaptive optics popup, CNN-AO tab",
        context="controller",
        runner=_capture_popup_adaptive_optics_cnn_ao,
    ),
    CaptureSpec(
        name="stage-control-start-pos-zstack",
        group="acquiring-data",
        description="Stage tab at Z-stack start position",
        context="controller",
        runner=_capture_stage_control_start_pos_zstack,
    ),
    CaptureSpec(
        name="press-start-pos",
        group="acquiring-data",
        description="Stack acquisition frame after setting Z-stack start",
        context="controller",
        runner=_capture_press_start_pos,
    ),
    CaptureSpec(
        name="stage-control-end-pos-zstack",
        group="acquiring-data",
        description="Stage tab at Z-stack end position",
        context="controller",
        runner=_capture_stage_control_end_pos_zstack,
    ),
    CaptureSpec(
        name="press-end-pos",
        group="acquiring-data",
        description="Stack acquisition frame after setting Z-stack end",
        context="controller",
        runner=_capture_press_end_pos,
    ),
    CaptureSpec(
        name="define-step-size",
        group="acquiring-data",
        description="Stack acquisition frame with step size entry selected",
        context="controller",
        runner=_capture_define_step_size,
    ),
    CaptureSpec(
        name="laser-cycling-settings",
        group="acquiring-data",
        description="Laser cycling combobox dropdown in stack acquisition settings",
        context="controller",
        runner=_capture_laser_cycling_settings,
    ),
    CaptureSpec(
        name="z-stack-acquisition",
        group="acquiring-data",
        description="Acquire mode dropdown opened on Z-Stack",
        context="controller",
        runner=_capture_z_stack_acquisition,
    ),
    CaptureSpec(
        name="configurator",
        group="configurator",
        description="Configuration assistant window",
        context="configurator",
        runner=_capture_configurator,
    ),
    CaptureSpec(
        name="multiposition-tissue",
        group="smart-routines",
        description="Main window with multiposition tab and first row selected",
        context="controller",
        runner=_capture_multiposition_tissue,
    ),
    CaptureSpec(
        name="multiposition-empty",
        group="smart-routines",
        description="Main window with multiposition tab and second row selected",
        context="controller",
        runner=_capture_multiposition_empty,
    ),
    CaptureSpec(
        name="feature-gui-1",
        group="smart-routines",
        description="Feature list popup with initial PrepareNextChannel node",
        context="controller",
        runner=_capture_feature_gui_1,
    ),
    CaptureSpec(
        name="feature-gui-2",
        group="smart-routines",
        description="Feature list popup with context menu near the first node",
        context="controller",
        runner=_capture_feature_gui_2,
    ),
    CaptureSpec(
        name="feature-gui-3",
        group="smart-routines",
        description="Feature list popup with duplicated PrepareNextChannel node",
        context="controller",
        runner=_capture_feature_gui_3,
    ),
    CaptureSpec(
        name="feature-gui-4",
        group="smart-routines",
        description="Feature selection/config popup for second node",
        context="controller",
        runner=_capture_feature_gui_4,
    ),
    CaptureSpec(
        name="feature-gui-5",
        group="smart-routines",
        description="Feature list popup with MoveToNextPosition node",
        context="controller",
        runner=_capture_feature_gui_5,
    ),
    CaptureSpec(
        name="feature-gui-6",
        group="smart-routines",
        description="Feature list popup with DetectTissueInStackAndReturn node",
        context="controller",
        runner=_capture_feature_gui_6,
    ),
    CaptureSpec(
        name="feature-gui-7",
        group="smart-routines",
        description="Feature list popup with LoopByCount added",
        context="controller",
        runner=_capture_feature_gui_7,
    ),
    CaptureSpec(
        name="feature-gui-8",
        group="smart-routines",
        description="Feature list popup with loop grouping parentheses",
        context="controller",
        runner=_capture_feature_gui_8,
    ),
    CaptureSpec(
        name="feature-gui-9",
        group="smart-routines",
        description="Feature list popup with DetectTissue decision node",
        context="controller",
        runner=_capture_feature_gui_9,
    ),
    CaptureSpec(
        name="feature-gui-10",
        group="smart-routines",
        description="Decision-node configuration popup with true/false branches",
        context="controller",
        runner=_capture_feature_gui_10,
    ),
]

CAPTURE_INDEX = {spec.name: spec for spec in CAPTURES}
GROUPS = sorted({spec.group for spec in CAPTURES})
DEFAULT_MANIFEST = [spec.name for spec in CAPTURES]
CONTEXT_BUILDERS = {
    "controller": _build_controller_context,
    "configurator": _build_configurator_context,
}
CONTEXT_CLEANUP = {
    "controller": _cleanup_controller_context,
    "configurator": _cleanup_configurator_context,
}


def _load_manifest(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return [str(item) for item in payload]
    if isinstance(payload, dict) and isinstance(payload.get("captures"), list):
        return [str(item) for item in payload["captures"]]
    raise ValueError("Manifest must be a JSON list or an object with a captures list.")


def _resolve_selection(cli_args: argparse.Namespace) -> List[str]:
    if cli_args.configurator_only:
        return ["configurator"]

    if cli_args.manifest:
        selected = _load_manifest(cli_args.manifest)
    elif cli_args.all or (not cli_args.group and not cli_args.capture):
        selected = list(DEFAULT_MANIFEST)
    else:
        selected = []
        if cli_args.group:
            group_set = set(cli_args.group)
            selected.extend(
                [spec.name for spec in CAPTURES if spec.group in group_set]
            )
        selected.extend(cli_args.capture)

    deduped = []
    seen = set()
    for name in selected:
        if name not in seen:
            deduped.append(name)
            seen.add(name)

    unknown = [name for name in deduped if name not in CAPTURE_INDEX]
    if unknown:
        raise ValueError(
            f"Unknown capture id(s): {', '.join(unknown)}. "
            "Use --list to see valid ids."
        )
    return deduped


def _list_available() -> None:
    print("Groups:")
    for group in GROUPS:
        print(f"  - {group}")
    print("\nCaptures:")
    for spec in CAPTURES:
        print(f"  - {spec.name:<22} [{spec.group}] {spec.description}")


def run(cli_args: argparse.Namespace) -> int:
    if cli_args.list:
        _list_available()
        return 0

    selected = _resolve_selection(cli_args)
    active_context_name = None
    active_context = None
    captured: List[Tuple[str, str]] = []

    try:
        for name in selected:
            spec = CAPTURE_INDEX[name]
            if spec.context != active_context_name:
                if active_context_name is not None and active_context is not None:
                    CONTEXT_CLEANUP[active_context_name](active_context)
                    active_context = None
                active_context = CONTEXT_BUILDERS[spec.context]()
                active_context_name = spec.context

            out_path = spec.runner(active_context, cli_args)
            captured.append((name, out_path))
            print(f"[capture] {name} -> {out_path}")
    finally:
        if active_context_name is not None and active_context is not None:
            CONTEXT_CLEANUP[active_context_name](active_context)

    print(f"[done] Captured {len(captured)} screenshot(s).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture navigate screenshots for documentation."
    )
    parser.add_argument(
        "--list", action="store_true", help="List available capture ids and groups."
    )
    parser.add_argument(
        "--all", action="store_true", help="Run the default manifest of all captures."
    )
    parser.add_argument(
        "--group",
        action="append",
        default=[],
        choices=GROUPS,
        help="Run all captures in a group (repeatable).",
    )
    parser.add_argument(
        "--capture",
        action="append",
        default=[],
        choices=sorted(CAPTURE_INDEX.keys()),
        help="Run a specific capture id (repeatable).",
    )
    parser.add_argument(
        "--manifest",
        help="Path to JSON manifest (list of capture ids, or {\"captures\": [...]})",
    )
    parser.add_argument(
        "--output-root",
        default=DEFAULT_OUTPUT_ROOT,
        help="Base output directory for capture paths (default: docs/source/images).",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=4,
        help="Number of settle/update passes before each screenshot.",
    )
    parser.add_argument(
        "--delay-ms",
        type=int,
        default=200,
        help="Delay (ms) between settle/update passes.",
    )
    # Backward-compatible shortcut.
    parser.add_argument(
        "--configurator-only",
        action="store_true",
        help="Capture only the configurator screenshot.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
