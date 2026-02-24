#!/usr/bin/env python3

"""Capture navigate GUI screenshots for documentation.

This module uses a capture registry plus CLI selectors so screenshots can be
updated in focused batches or all at once.
"""

import argparse
import json
import os
import sys
import tkinter as tk
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

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
    _prepare_for_capture(ctx["root"], cli_args)
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

    parser = create_parser()
    args = parser.parse_args(["-sh"])

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
        _prepare_for_capture(ctx["root"], cli_args)
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


CAPTURES: List[CaptureSpec] = [
    CaptureSpec(
        name="main-window",
        group="main-ui",
        description="Main navigate application window",
        context="controller",
        runner=_capture_main_window,
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
        name="settings-stage-control",
        group="main-ui",
        description="Stage control settings notebook tab",
        context="controller",
        runner=lambda ctx, args: _capture_settings_tab(ctx, args, "stage_control_tab"),
    ),
    CaptureSpec(
        name="settings-multiposition",
        group="main-ui",
        description="Multiposition settings notebook tab",
        context="controller",
        runner=lambda ctx, args: _capture_settings_tab(ctx, args, "multiposition_tab"),
    ),
    CaptureSpec(
        name="camera-tab",
        group="main-ui",
        description="Camera display tab",
        context="controller",
        runner=lambda ctx, args: _capture_camera_tab(ctx, args, "camera_tab"),
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
