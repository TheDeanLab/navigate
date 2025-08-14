from mss import mss
from PIL import Image
import tkinter as tk
import os
from navigate.view.splash_screen import SplashScreen
from navigate.controller.controller import Controller
from navigate.tools.main_functions import create_parser, evaluate_parser_input_arguments


def get_controller():
    root = tk.Tk()
    root.withdraw()

    # Create splash screen
    current_directory = os.path.dirname(os.path.realpath(__file__))
    splash_screen = SplashScreen(
        root,
        os.path.join(
            current_directory,
            "..",
            "navigate",
            "view",
            "icon",
            "splash_screen_image.png",
        ),
    )

    # Parse arguments with -sh flag
    parser = create_parser()
    args = parser.parse_args(["-sh"])

    # Get paths from arguments
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

    # Create and return controller
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
        args,
    )

    return root, controller


def capture_region(x, y, w, h, out_path):
    with mss() as sct:
        img = sct.grab(
            {"left": int(x), "top": int(y), "width": int(w), "height": int(h)}
        )
        Image.frombytes("RGB", img.size, img.rgb).save(out_path)


def tk_window_bbox(win, pad=0):
    win.update_idletasks()
    x = win.winfo_rootx() - pad
    y = win.winfo_rooty() - pad
    w = win.winfo_width() + 2 * pad
    h = win.winfo_height() + 2 * pad
    return x, y, w, h


if __name__ == "__main__":
    root, controller = get_controller()
    current_directory = os.path.dirname(os.path.realpath(__file__))

    # Main Window
    bbox = tk_window_bbox(controller.view)
    save_path = os.path.join(
        current_directory, f"{controller.view.__class__.__name__}.png"
    )
    capture_region(*bbox, out_path=save_path)
    root.update()

    # Settings Tabs
    for tab in [
        controller.view.settings.camera_settings_tab,
        controller.view.settings.channels_tab,
        controller.view.settings.stage_control_tab,
        controller.view.settings.multiposition_tab,
    ]:
        controller.view.settings.select(tab)
        root.update()
        bbox = tk_window_bbox(controller.view.settings)
        save_path = os.path.join(current_directory, f"{tab.__class__.__name__}.png")
        capture_region(*bbox, out_path=save_path)

    # Camera Tabs
    for tab in [
        controller.view.camera_waveform.camera_tab,
        # controller.view.camera_waveform.waveform_tab,
        controller.view.camera_waveform.mip_tab,
    ]:
        controller.view.camera_waveform.select(tab)
        root.update()
        bbox = tk_window_bbox(controller.view.camera_waveform)
        save_path = os.path.join(current_directory, f"{tab.__class__.__name__}.png")
        capture_region(*bbox, out_path=save_path)
