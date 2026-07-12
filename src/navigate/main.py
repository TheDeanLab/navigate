# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Standard Library Imports
import tkinter as tk
import logging
import platform
import os
import sys
from typing import Optional

# Third Party Imports

# Local Imports
from navigate.controller.controller import Controller
from navigate.controller.configurator import Configurator
from navigate.log_files.log_functions import log_setup
from navigate.view.splash_screen import SplashScreen
from navigate.tools.main_functions import (
    evaluate_parser_input_arguments,
    create_parser,
)

logger = logging.getLogger(__name__)

VIEWER_IMPORT_TO_DISTRIBUTION = {
    "OpenGL": "PyOpenGL",
    "glfw": "glfw",
    "glm": "PyGLM",
    "tkinterdnd2": "tkinterdnd2",
}

# Proxy Configuration
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""


def _missing_viewer_distribution(error: BaseException) -> Optional[str]:
    """Return the installable package name associated with an import error."""
    module_name = getattr(error, "name", None)
    if not module_name:
        return None
    root_name = str(module_name).split(".", 1)[0]
    return VIEWER_IMPORT_TO_DISTRIBUTION.get(root_name, str(module_name))


def _build_volume_viewer_error_message(error: BaseException) -> str:
    """Build beginner-oriented recovery instructions for viewer import failures."""
    python_command = f'"{sys.executable}"'
    distribution = _missing_viewer_distribution(error)
    dependency_line = (
        f"Missing or unavailable Python package: {distribution}."
        if distribution
        else "An optional viewer dependency could not be loaded."
    )
    return "\n".join(
        [
            "Unable to start the optional navigate Volume Viewer.",
            "The standard navigate application is still available.",
            "",
            dependency_line,
            "The Volume Viewer dependencies are not included in a standard installation.",
            "If you use Conda or a virtual environment, activate the environment",
            "that you normally use to run navigate before installing anything.",
            "",
            "From a navigate source checkout, run:",
            f'  {python_command} -m pip install -e ".[opengl]"',
            "",
            "If navigate was installed as a package, run:",
            f'  {python_command} -m pip install "navigate-micro[opengl]"',
            "",
            "Then retry:",
            "  navigate --viewer",
            "",
            "If the viewer still does not start, check the navigate log and report",
            "the technical error shown below:",
            f"  {type(error).__name__}: {error}",
        ]
    )


def _load_volume_viewer() -> Optional[type]:
    """Load the optional volume viewer and report actionable import failures."""
    try:
        from navigate.view.display_backends.volume_viewer_standalone import (
            VolumeViewer,
        )
    except (ImportError, OSError) as error:
        logger.exception("Unable to import the optional Volume Viewer")
        print(_build_volume_viewer_error_message(error), file=sys.stderr)
        return None
    return VolumeViewer


def main():
    """Light-sheet Microscopy (Navigate).
    Microscope control software built in a Model-View-Controller architecture.
    Provides control of cameras, data acquisition cards, filter wheels, lasers
    stages, voice coils, and zoom servos.

    Parameters
    ----------
    *args : iterable
        --synthetic-hardware
        --sh
        --config-file
        --experiment-file
        --waveform_constants-path
        --rest-api-file
        --waveform-templates-file
        --logging-confi
        --configurator
    """
    if platform.system() != "Windows":
        print(
            "WARNING: navigate was built to operate on a Windows platform. "
            "While much of the software will work for evaluation purposes, some "
            "unanticipated behaviors may occur."
        )

    # Start the GUI, withdraw main screen, and show splash screen.
    root = tk.Tk()
    root.withdraw()

    # Splash Screen
    current_directory = os.path.dirname(os.path.realpath(__file__))
    splash_screen = SplashScreen(
        root, os.path.join(current_directory, "view", "icon", "splash_screen_image.png")
    )

    # Parse command line arguments
    parser = create_parser()
    command_line_args = parser.parse_args()

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
    ) = evaluate_parser_input_arguments(command_line_args)

    # Configure logging with the multiprocess listener
    log_queue, log_listener = log_setup(
        "logging.yml", logging_path, start_listener=True
    )

    if command_line_args.configurator:
        Configurator(root, splash_screen)
    elif command_line_args.viewer:
        volume_viewer_class = _load_volume_viewer()
        if volume_viewer_class is None:
            for startup_window in (splash_screen, root):
                try:
                    startup_window.destroy()
                except Exception:
                    logger.debug(
                        "Unable to destroy viewer startup window",
                        exc_info=True,
                    )
            log_listener.stop()
            return

        volume_viewer = volume_viewer_class(root=root, splash_screen=splash_screen)

        # Replace the root with volume viewer
        root = volume_viewer
    else:
        Controller(
            root=root,
            splash_screen=splash_screen,
            configuration_path=configuration_path,
            experiment_path=experiment_path,
            waveform_constants_path=waveform_constants_path,
            rest_api_path=rest_api_path,
            waveform_templates_path=waveform_templates_path,
            gui_configuration_path=gui_configuration_path,
            multi_positions_path=multi_positions_path,
            log_queue=log_queue,
            args=command_line_args,
        )

    root.mainloop()
    log_listener.stop()


if __name__ == "__main__":
    main()
