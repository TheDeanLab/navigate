# Copyright (c) 2021-2023  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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
#

import random


def test_change_resolution(model):
    """
    Note: The stage position check is an absolute mess due to us instantiating two
    SyntheticStages--one for each microsocpe. We have to continuously reset the
    stage positions to all zeros and make the configuration.yaml that comes with the
    software have negative stage bounds.
    """
    scopes = random.choices(
        model.configuration["configuration"]["microscopes"].keys(), k=10
    )
    zooms = [
        random.choice(
            model.configuration["configuration"]["microscopes"][scope]["zoom"][
                "position"
            ].keys()
        )
        for scope in scopes
    ]
    axes = ["x", "y", "z", "theta", "f"]

    for scope, zoom in zip(scopes, zooms):
        former_offset_dict = model.configuration["configuration"]["microscopes"][
            model.configuration["experiment"]["MicroscopeState"]["microscope_name"]
        ]["stage"]
        # reset stage axes to all zeros, to match default SyntheticStage behaviour
        for ax in axes:
            model.active_microscope.stages[ax].move_absolute(
                {ax + "_abs": 0}, wait_until_done=True
            )
        former_pos_dict = model.get_stage_position()
        print(f"{model.active_microscope_name}: {former_pos_dict}")

        print(
            f"CHANGING {model.active_microscope_name} at"
            '{model.configuration["experiment"]["MicroscopeState"]["zoom"]} to {scope}'
            "at {zoom}"
        )
        model.configuration["experiment"]["MicroscopeState"]["microscope_name"] = scope
        model.configuration["experiment"]["MicroscopeState"]["zoom"] = zoom
        model.change_resolution(scope)

        self_offset_dict = model.configuration["configuration"]["microscopes"][scope][
            "stage"
        ]
        pos_dict = model.get_stage_position()

        print(f"{model.active_microscope_name}: {pos_dict}")

        # reset stage axes to all zeros, to match default SyntheticStage behaviour
        for ax in model.active_microscope.stages:
            print(f"axis {ax}")
            assert (
                pos_dict[ax + "_pos"]
                - self_offset_dict[ax + "_offset"]
                + former_offset_dict[ax + "_offset"]
            ) == 0

        for ax in axes:
            model.active_microscope.stages[ax].move_absolute(
                {ax + "_abs": 0}, wait_until_done=True
            )

        assert model.active_microscope_name == scope
        assert model.active_microscope.zoom.zoomvalue == zoom
