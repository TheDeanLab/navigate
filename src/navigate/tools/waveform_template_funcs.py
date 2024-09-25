# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

# Standard library imports

# Third-party imports

# Local application imports


def get_waveform_template_parameters(
    waveform_template_name, waveform_template_dict, microscope_state_dict
):
    """this function will get the parameters of a waveform template

    Parameters
    ----------
    waveform_template_name: str
        the name of the waveform template
    waveform_template_dict: dict
        the dictionary of the waveform templates
    microscope_state_dict: dict
        the dictionary of the microscope state

    Returns
    -------
    repeat_num: int
        the number of repeats
    expand_num: int
        the number of expands
    """
    try:
        waveform_template = waveform_template_dict[waveform_template_name]
    except KeyError:
        repeat_num, expand_num = 1, 1
        return repeat_num, expand_num

    try:
        if type(waveform_template["repeat"]) is int:
            repeat_num = waveform_template["repeat"]
        else:
            repeat_num = int(microscope_state_dict[waveform_template["repeat"]])
    except KeyError:
        repeat_num = 1

    try:
        if type(waveform_template["expand"]) is int:
            expand_num = waveform_template["expand"]
        else:
            expand_num = int(microscope_state_dict[waveform_template["expand"]])
    except KeyError:
        expand_num = 1

    return repeat_num, expand_num
