"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
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
# """

# Third Party Imports
import pytest

from aslm.model.devices.camera.camera_base import CameraBase


def test_start_camera(dummy_model):
    model = dummy_model
    for microscope_name in model.configuration["configuration"]["microscopes"].keys():
        camera = CameraBase(microscope_name, None, model.configuration)
        assert (
            camera.camera_parameters["hardware"]["serial_number"]
            == model.configuration["configuration"]["microscopes"][microscope_name][
                "camera"
            ]["hardware"]["serial_number"]
        ), f"didn't load correct camera parameter for microscope {microscope_name}"

    # non-exist microscope name
    microscope_name = (
        model.configuration["configuration"]["microscopes"].keys()[0] + "_random_error"
    )
    raised_error = False
    try:
        camera = CameraBase(microscope_name, None, model.configuration)
    except NameError:
        raised_error = True
    assert (
        raised_error
    ), "should raise NameError when the microscope name doesn't exist!"


def test_camera_base_functions(dummy_model):
    import random

    model = dummy_model
    microscope_name = model.configuration["experiment"]["MicroscopeState"][
        "microscope_name"
    ]

    camera = CameraBase(microscope_name, None, model.configuration)
    funcs = ["set_readout_direction", "calculate_light_sheet_exposure_time"]
    args = [[random.random()], [random.random(), random.random()]]

    for f, a in zip(funcs, args):
        if a is not None:
            getattr(camera, f)(*a)
        else:
            getattr(camera, f)()
