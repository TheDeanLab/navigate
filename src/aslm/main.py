# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
from aslm.controller.controller import Controller
from aslm.log_files.log_functions import log_setup
from aslm.view.splash_screen import SplashScreen
from aslm.tools.main_functions import (
    identify_gpu,
    evaluate_parser_input_arguments,
    create_parser,
)

# Proxy Configuration
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""


def main():
    """Autonomous Software for Light Microscopy (ASLM).
    Microscope control software built in a Model-View-Controller architecture.
    Provides control of cameras, data acquisition cards, filter wheels, lasers
    stages, voice coils, and zoom servos.

    Parameters
    ----------
    *args : iterable
        --synthetic_hardware
        --sh
        --debug
        --CPU
        --config_file
        --experiment_file
        --etl_const_file
        --rest_api_file
        --logging_config

    Examples
    --------
    python main.py --synthetic_hardware
    """
    # Start the GUI, withdraw main screen, and show splash screen.
    root = tk.Tk()
    root.withdraw()
    splash_screen = SplashScreen(root, "./icon/splash_screen_image.png")

    # Parse command line arguments
    parser = create_parser()
    args = parser.parse_args()

    print(f"Args type: {type(args)}")

    (
        configuration_path,
        experiment_path,
        etl_constants_path,
        rest_api_path,
        logging_path,
    ) = evaluate_parser_input_arguments(args)

    log_setup("logging.yml")
    use_gpu = identify_gpu(args)

    Controller(
        root,
        splash_screen,
        configuration_path,
        experiment_path,
        etl_constants_path,
        rest_api_path,
        use_gpu,
        args,
    )
    root.mainloop()


if __name__ == "__main__":
    if platform.system() == "Darwin":
        print(
            "Apple OS Not Fully Supported. ",
            "Tensorflow and CuPy based analysis is not possible. ",
            "Please try Linux or Windows for this functionality",
        )

    main()
