# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

"""
This stores functions that are update the dictionary common to aslm.model and aslm.controller.
"""


def update_settings_common(target, args):
    """
    Update dictionary entries common to the model and controller. This helps us percolate changes through the
    copies of the dictionaries in each major object.
    """
    if args[0] == "channel":
        target.configuration["experiment"]["MicroscopeState"]["channels"] = args[1]

    if args[0] == "resolution":
        """
        args[1] is a dictionary that includes 'resolution_mode': 'low', 'zoom': '1x', 'laser_info': ...
        ETL popup window updating the self.etl_constants.
        Passes new self.etl_constants to the self.model.daq
        TODO: Make sure the daq knows which etl data to use based upon wavelength, zoom, resolution mode, etc.
        """
        updated_settings = args[1]
        resolution_mode = updated_settings["resolution_mode"]
        zoom = updated_settings["zoom"]
        laser_info = updated_settings["laser_info"]

        if resolution_mode == "low":
            target.configuration["etl_constants"]["ETLConstants"]["low"][
                zoom
            ] = laser_info
        else:
            target.configuration["etl_constants"]["ETLConstants"]["high"][
                zoom
            ] = laser_info
        # if target.verbose:
        #     print(target.etl_constants['ETLConstants']['low'][zoom])

        # Modify DAQ to pull the initial values from the waveform_constants.yml file, or be passed it from the model.
        # Pass to the self.model.daq to
        #             value = self.resolution_info['ETLConstants'][self.resolution][self.mag][laser][remote_focus_name]
        # print(args[1])

    if args[0] == "galvo":
        ((param, value),) = args[1].items()
        target.configuration["experiment"]["GalvoParameters"][param] = value

    if args[0] == "number_of_pixels":
        target.configuration["experiment"]["CameraParameters"][
            "number_of_pixels"
        ] = args[1]


def update_stage_dict(target, pos_dict):
    # Update our local experiment parameters
    for axis, val in pos_dict.items():
        ax = axis.split("_")[0]
        target.configuration["experiment"]["StageParameters"][ax] = val
