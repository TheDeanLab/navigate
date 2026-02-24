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
from typing import Callable, Dict, List, Tuple

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
    for _ in range(passes):
        root.update_idletasks()
        idle_done = {"value": False}
        root.after_idle(lambda: idle_done.update(value=True))
        while not idle_done["value"]:
            root.update()
        root.after(delay_ms)
        root.update()


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


def _capture_main_window(ctx: Dict[str, object], cli_args: argparse.Namespace) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    settle_window(root, passes=cli_args.passes, delay_ms=cli_args.delay_ms)
    out_path = os.path.join(
        cli_args.output_root, f"{controller.view.__class__.__name__}.png"
    )
    return _capture_widget(controller.view, out_path)


def _capture_settings_tab(
    ctx: Dict[str, object], cli_args: argparse.Namespace, attr_name: str
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    tab = getattr(controller.view.settings, attr_name)
    controller.view.settings.select(tab)
    settle_window(root, passes=cli_args.passes, delay_ms=cli_args.delay_ms)
    out_path = os.path.join(cli_args.output_root, f"{tab.__class__.__name__}.png")
    return _capture_widget(controller.view.settings, out_path)


def _capture_channel_selector(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    channels_tab = controller.view.settings.channels_tab
    controller.view.settings.select(channels_tab)
    settle_window(root, passes=cli_args.passes, delay_ms=cli_args.delay_ms)
    out_path = os.path.join(cli_args.output_root, "channel-selector.png")
    return _capture_widget(channels_tab.channel_widgets_frame, out_path, pad=2)


def _capture_channel_selector_filter_dropdown(
    ctx: Dict[str, object], cli_args: argparse.Namespace
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    channels_tab = controller.view.settings.channels_tab
    controller.view.settings.select(channels_tab)
    settle_window(root, passes=cli_args.passes, delay_ms=cli_args.delay_ms)

    frame = channels_tab.channel_widgets_frame
    if not frame.filterwheel_pulldowns:
        raise RuntimeError("No filter wheel combobox widgets available to capture.")

    filter_combo = frame.filterwheel_pulldowns[0]
    values = filter_combo.cget("values")
    if values:
        # Ensure the combobox shows a concrete value in the field.
        filter_combo.set(values[0])

    popup_path = None
    try:
        filter_combo.focus_set()
        root.tk.call("ttk::combobox::Post", filter_combo)
        settle_window(root, passes=max(3, cli_args.passes), delay_ms=cli_args.delay_ms)
        popup_path = str(root.tk.call("ttk::combobox::PopdownWindow", filter_combo))
    except tk.TclError:
        # Fallback: click-open behavior if the Tcl Post command is unavailable.
        filter_combo.event_generate("<Button-1>")
        settle_window(root, passes=max(3, cli_args.passes), delay_ms=cli_args.delay_ms)
        try:
            popup_path = str(root.tk.call("ttk::combobox::PopdownWindow", filter_combo))
        except tk.TclError:
            popup_path = None

    frame_bbox = tk_window_bbox(frame, pad=2)
    if popup_path:
        try:
            popup_bbox = _bbox_from_path(root, popup_path, pad=2)
            bbox = _union_bbox(frame_bbox, popup_bbox)
        except tk.TclError:
            bbox = frame_bbox
    else:
        bbox = frame_bbox

    out_path = os.path.join(cli_args.output_root, "channel-selector-filter.png")
    captured = _capture_bbox(bbox, out_path)

    try:
        root.tk.call("ttk::combobox::Unpost", filter_combo)
    except tk.TclError:
        pass
    settle_window(root, passes=1, delay_ms=cli_args.delay_ms)
    return captured


def _capture_camera_tab(
    ctx: Dict[str, object], cli_args: argparse.Namespace, attr_name: str
) -> str:
    root = ctx["root"]
    controller = ctx["controller"]
    tab = getattr(controller.view.camera_waveform, attr_name)
    controller.view.camera_waveform.select(tab)
    settle_window(root, passes=cli_args.passes, delay_ms=cli_args.delay_ms)
    out_path = os.path.join(cli_args.output_root, f"{tab.__class__.__name__}.png")
    return _capture_widget(controller.view.camera_waveform, out_path)


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
