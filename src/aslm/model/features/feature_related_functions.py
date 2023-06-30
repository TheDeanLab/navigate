# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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
from aslm.model.features.auto_tile_scan import CalculateFocusRange
from aslm.model.features.autofocus import Autofocus
from aslm.model.features.common_features import (
    ChangeResolution,
    Snap,
    WaitToContinue,
    LoopByCount,
    PrepareNextChannel,
    MoveToNextPositionInMultiPostionTable,
    StackPause,
    ZStackAcquisition,
    ConProAcquisition,
    FindTissueSimple2D,
)
from aslm.model.features.image_writer import ImageWriter
from aslm.model.features.restful_features import IlastikSegmentation
from aslm.model.features.volume_search import VolumeSearch

def convert_str_to_feature_list(content: str):
    try:
        exec_result = {}
        exec(f"result={content}", globals(), exec_result)
        if type(exec_result["result"]) is not list:
            print("Please make sure the feature list is a list!")
            return None
        return exec_result["result"]
    except Exception as e:
        print("Can't build this feature list!", e)
        return None
    
def convert_feature_list_to_str(feature_list):
    result = '['
    def f(feature_list):
        nonlocal result
        for item in feature_list:
            if type(item) is dict:
                result += '{' + f'"name": {item["name"].__name__},'
                if "args" in item:
                    result += f'"args":{str(item["args"])}'
                result += '},'
            elif type(item) is tuple:
                result += '('
                f(item)
                result += '),'
    
    f(feature_list)
    result += ']'
    return result
        


[{"name": Autofocus}, {"name": ZStackAcquisition}, {"name": StackPause},
 {"name": Autofocus}, {"name": ZStackAcquisition}, {"name": StackPause}]

[{"name": Autofocus}, {"name": ZStackAcquisition}, {"name": StackPause},
 ({"name": Autofocus}, ({"name": ZStackAcquisition}, {"name": LoopByCount}), {"name": LoopByCount}),
 {"name": Autofocus}, {"name": ZStackAcquisition}, {"name": StackPause}]

[{"name": Autofocus}, {"name": ZStackAcquisition}, {"name": StackPause},
 (({"name": ZStackAcquisition}, {"name": LoopByCount}), {"name": LoopByCount},
({"name": ZStackAcquisition}, {"name": LoopByCount}), {"name": LoopByCount}
),
 {"name": Autofocus}, {"name": ZStackAcquisition}, {"name": StackPause}]

[{"name": Autofocus}, {"name": ZStackAcquisition}, {"name": StackPause},
 ((({"name": ZStackAcquisition}, {"name": LoopByCount}), {"name": LoopByCount},
({"name": ZStackAcquisition}, {"name": LoopByCount}), {"name": LoopByCount}),

{"name": LoopByCount}),
 {"name": Autofocus}, {"name": ZStackAcquisition}, {"name": StackPause}]
