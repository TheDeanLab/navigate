from aslm.tools.decorators import FeatureList
from aslm.model.features.common_features import *
from aslm.model.features.remove_empty_tiles import *
from aslm.model.features.auto_tile_scan import *
from aslm.model.features.feature_related_functions import SharedList

@FeatureList
def test_feature_1():
    return [
                (
                    {"name": PrepareNextChannel},
                    {
                        "name": LoopByCount,
                        "args": ("experiment.MicroscopeState.selected_channels",),
                    },
                )
            ]


@FeatureList
def test_feature_2():
    return [{"name": PrepareNextChannel}]

def detect_func():
    return False

@FeatureList
def test_remove_empty_tiles():    
    records = SharedList([1, 2, 3, "a", "b", "c"], name="records")

    return [
        (
            {"name": MoveToNextPositionInMultiPostionTable},
            {"name": CalculateFocusRange},
            {
                "name": DetectTissueInStackAndRecord,
                "args": (
                    5,
                    0.75,
                    detect_func,
                    records,
                ),
            },
            {
                "name": LoopByCount,
                "args": ("experiment.MicroscopeState.multiposition_count",),
            },
        ),
        {
            "name": RemoveEmptyPositions,
            "args": (
                records,
            )
        }
    ]
