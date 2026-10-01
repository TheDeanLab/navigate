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

from multiprocessing.managers import ListProxy

from navigate.config.preload import PreloadContext, PreloadRule


def validate_multi_positions(context: PreloadContext) -> None:
    """Validate optional multi-position data."""
    context.configuration["multi_positions"] = validate_positions(
        context.multi_positions
    )


def validate_positions(positions) -> list:
    """Return multi-position rows with invalid rows removed.

    A full header row containing both ``X`` and ``Y`` is preserved. A partial header
    row containing only one of those fields is discarded before value validation.
    """
    if positions is None or type(positions) not in (list, ListProxy):
        return []

    positions = list(positions)
    start_index = _position_data_start_index(positions)
    if start_index == len(positions):
        return []

    valid_positions = positions[:start_index]
    for position in positions[start_index:]:
        if _is_valid_position_row(position):
            valid_positions.append(position)
    return valid_positions


def _position_data_start_index(positions) -> int:
    """Return the first index that should contain numeric position values."""
    if len(positions) == 0:
        return 0
    try:
        cmp_header = [axis in positions[0] for axis in ["X", "Y"]]
    except TypeError:
        return 0
    if all(cmp_header):
        return 1
    if any(cmp_header):
        del positions[0]
    return 0


def _is_valid_position_row(position) -> bool:
    """Return whether every value in one multi-position row can be parsed as float."""
    try:
        for value in position:
            float(value)
    except (TypeError, ValueError, KeyError, IndexError):
        return False
    return True


POSITIONS_RULES = [
    PreloadRule("positions", "multi_positions", validate_multi_positions),
]
