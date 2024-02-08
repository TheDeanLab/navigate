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


def update_nested_dict(d, find_func, apply_func):
    """ Update a nested dictionary by applying a function to a value

    Loops through a nested dictionary and if find_func() conditions are met,
    run apply_func on that key.

    TODO: It might be nice to make this non-recursive.

    Parameters
    ----------
    d : dict
        Dictionary to be updated
    find_func : func
        Accepts key, value pair and matches a condition based on these. Returns bool.
    apply_func : func
        Accepts a value returns the new value.

    Returns
    -------
    d2 : dict
        An version of d, updated according to the passed functions.
    """
    d2 = {}
    for k, v in d.items():
        if find_func(k, v):
            d2[k] = apply_func(v)
        else:
            d2[k] = v
        if isinstance(v, dict):
            d2[k] = update_nested_dict(v, find_func, apply_func)
    return d2


def update_stage_dict(target, pos_dict):
    """Update dictionary entries common to the model and controller.

    Parameters
    ----------
    target : navigate.model.Model or navigate.controller.Controller
        The object that is being updated.
    pos_dict : dict
        The dictionary of positions to update.

    Returns
    -------
    None
    """
    # Update our local experiment parameters
    for axis, val in pos_dict.items():
        ax = axis.split("_")[0]
        target.configuration["experiment"]["StageParameters"][ax] = val
