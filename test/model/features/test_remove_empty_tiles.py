import numpy as np

from navigate.model.features.feature_related_functions import SharedList
from navigate.model.features.remove_empty_tiles import (
    DetectTissueInStack,
    DetectTissueInStackAndRecord,
    DetectTissueInStackAndReturn,
    detect_tissue3,
)


class _Logger:
    def debug(self, *args, **kwargs):
        pass


class _Model:
    def __init__(self):
        self.data_buffer = {}
        self.logger = _Logger()


def test_return_detector_preserves_legacy_positional_arguments():
    feature = DetectTissueInStackAndReturn(_Model(), 1, 0.5, None)

    assert feature.planes == 1
    assert feature.percentage == 0.5
    assert feature.threshold == 150
    assert feature.detect_func is detect_tissue3


def test_record_detector_preserves_legacy_positional_records_argument():
    records = SharedList([], "records")

    feature = DetectTissueInStackAndRecord(_Model(), 5, 0.75, records)

    assert feature.planes == 5
    assert feature.percentage == 0.75
    assert feature.threshold == 150
    assert feature.position_records is records


def test_record_detector_default_records_are_not_shared():
    first = DetectTissueInStackAndRecord(_Model())
    second = DetectTissueInStackAndRecord(_Model())

    first.position_records.append(True)

    assert second.position_records == []


def test_stack_decision_uses_percentage_of_tissue_positive_frames():
    model = _Model()
    model.data_buffer = {0: False, 1: True, 2: True}
    feature = DetectTissueInStack(
        model,
        planes=3,
        percentage=2 / 3,
        detect_func=lambda frame, threshold: frame,
    )
    feature.pre_func_data()

    assert not feature.in_func_data([0, 1])
    assert feature.in_func_data([2])


def test_detect_tissue3_documents_computed_otsu_threshold_contract():
    assert "computed Otsu threshold" in (detect_tissue3.__doc__ or "")

    image_data = np.full((4, 4), 200, dtype=np.uint16)

    assert detect_tissue3(image_data, threshold=150)
