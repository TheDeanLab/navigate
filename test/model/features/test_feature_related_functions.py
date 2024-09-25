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

# Third party imports
import pytest

# local imports
from navigate.model.features.feature_related_functions import (
    convert_str_to_feature_list,
    convert_feature_list_to_str,
)
from navigate.model.features.common_features import (
    PrepareNextChannel,
    LoopByCount,
    ZStackAcquisition,
)


@pytest.mark.parametrize(
    "feature_list_str, expected_list",
    [
        ("", None),
        ("[]", []),
        ("[{'name': PrepareNextChannel}]", [{"name": PrepareNextChannel}]),
        ("[{'name': NonExistFeature}]", None),
        (
            "[({'name': PrepareNextChannel}, {'name': LoopByCount})]",
            [({"name": PrepareNextChannel}, {"name": LoopByCount})],
        ),
        (
            "[({'name': PrepareNextChannel}, {'name': LoopByCount, 'args': (3,)})]",
            [({"name": PrepareNextChannel}, {"name": LoopByCount, "args": (3,)})],
        ),
        (
            "[({'name': PrepareNextChannel}, {'name': LoopByCount, 'args': 3})]",
            [({"name": PrepareNextChannel}, {"name": LoopByCount, "args": (3,)})],
        ),
        (
            "[({'name': PrepareNextChannel}, {'name': LoopByCount, 'args': (3)})]",
            [({"name": PrepareNextChannel}, {"name": LoopByCount, "args": (3,)})],
        ),
        (
            "[(({'name': PrepareNextChannel}, {'name': LoopByCount, 'args': (3)}))]",
            [({"name": PrepareNextChannel}, {"name": LoopByCount, "args": (3,)})],
        ),
        (
            "[{'name': ZStackAcquisition, 'args': (True, False, 'zstack',)}]",
            [
                {
                    "name": ZStackAcquisition,
                    "args": (
                        True,
                        False,
                        "zstack",
                    ),
                }
            ],
        ),
    ],
)
def test_convert_str_to_feature_list(feature_list_str, expected_list):
    feature_list = convert_str_to_feature_list(feature_list_str)

    assert feature_list == expected_list


@pytest.mark.parametrize(
    "feature_list, expected_str",
    [
        (None, "[]"),
        ([], "[]"),
        ([{"name": PrepareNextChannel}], '[{"name": PrepareNextChannel,},]'),
        (
            [({"name": PrepareNextChannel}, {"name": LoopByCount})],
            '[({"name": PrepareNextChannel,},{"name": LoopByCount,},),]',
        ),
        (
            [({"name": PrepareNextChannel}, {"name": LoopByCount, "args": (3,)})],
            '[({"name": PrepareNextChannel,},{"name": LoopByCount,"args": (3,),},),]',
        ),
        (
            [
                {
                    "name": ZStackAcquisition,
                    "args": (
                        True,
                        False,
                        "zstack",
                    ),
                }
            ],
            '[{"name": ZStackAcquisition,"args": (True,False,"zstack",),},]',
        ),
    ],
)
def test_convert_feature_list_to_str(feature_list, expected_str):
    feature_str = convert_feature_list_to_str(feature_list)

    assert feature_str == expected_str

    if feature_list:
        assert convert_str_to_feature_list(feature_str) == feature_list
