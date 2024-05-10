# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
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

def slice_len(sl, n):
    """Calculate the length of the slice over an array of size n.

    Parameters
    ----------
    sl : slice
        The slice.
    n : int
        The size of the array.

    Returns
    -------
    int
        The length of the slice.
    """
    return len(range(n)[sl])

def key_len(keys):
    # Check lengths
    if isinstance(keys, slice) or isinstance(keys, int):
        length = 1
    else:
        length = len(keys)

    if length < 1:
        raise IndexError(
            "Too few indices."
        )

    return length

def ensure_iter(keys, pos, shape):
    """Ensure the output is iterable.

    Parameters
    ----------
    keys : int or tuple or list or array
        List of indices to slice an array.
    pos : int
        Index into keys.
    shape : int
        The length of the dimension we are slicing.

    Returns
    -------
    range
        The range.
    """
    length = key_len(keys)

    # Handle "slice the rest"
    if length > 1 and keys[-1] == Ellipsis:
        keys = keys[:-1]
        length -= 1

    if length > pos:
        try:
            val = keys[pos]
        except TypeError:
            # Only one key
            val = keys
        if isinstance(val, slice):
            if val.start is None and val.stop is None and val.step is None:
                return range(shape)
            tmp = range(10**10)[val]
            start, stop, step = tmp.start, tmp.stop, tmp.step
            if start > shape:
                start = shape
            if stop > shape:
                stop = shape
            return range(start, stop, step)
        elif isinstance(val, int):
            if val > shape or (val + 1) > shape:
                # TODO: It's not clear to me this is the correct behavior 
                return range(shape-1, shape)
            return range(val, val + 1)
            
    else:
        return range(shape)

def ensure_slice(keys, pos):
    """Ensure the output is a slice.

    Parameters
    ----------
    keys : int or tuple or list or array
        List of indices to slice an array.
    pos : int
        Index into keys.

    Returns
    -------
    slice
        The slice.
    """
    length = key_len(keys)

    # Handle "slice the rest"
    if length > 1 and keys[-1] == Ellipsis:
        keys = keys[:-1]
        length -= 1

    if length > pos:
        try:
            val = keys[pos]
        except TypeError:
            # Only one key
            val = keys
        if isinstance(val, int):
            return slice(val, val+1, None)
        assert isinstance(val, slice)
        return val
    else:
        # Default to all values
        return slice(None, None, None)