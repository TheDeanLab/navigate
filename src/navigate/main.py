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
import platform
import os

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

# Proxy Configuration
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""


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
    else:
        controller = Controller(
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
        if controller.startup_cancelled:
            splash_screen.destroy()
            root.destroy()
            log_listener.stop()
            return

    root.mainloop()
    log_listener.stop()


if __name__ == "__main__":
    main()
