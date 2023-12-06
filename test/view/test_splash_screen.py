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
import unittest
import tkinter as tk
from pathlib import Path

# Third Party Imports

# Local Imports
from navigate.view.splash_screen import SplashScreen


class TestSplashScreen(unittest.TestCase):
    def setUp(self):
        # Create a root Tkinter window for testing
        self.root = tk.Tk()

    def tearDown(self):
        # Destroy the root window after each test
        self.root.destroy()

    def test_splash_screen_with_image(self):
        # Create a SplashScreen instance with an image
        main_directory = Path(__file__).resolve().parent.parent.parent
        image_directory = Path.joinpath(
            main_directory, "src", "navigate", "view", "icon", "splash_screen_image.png"
        )

        splash_screen = SplashScreen(self.root, img_path=image_directory)
        # Replace 'your_image.png' with a valid image path

        # Check if the SplashScreen is an instance of tk.Toplevel
        self.assertIsInstance(splash_screen, tk.Toplevel)

    def test_splash_screen_without_image(self):
        # Create a SplashScreen instance without an image
        splash_screen = SplashScreen(self.root, "non_existent_image.png")

        # Check if the SplashScreen is an instance of tk.Toplevel
        self.assertIsInstance(splash_screen, tk.Toplevel)
