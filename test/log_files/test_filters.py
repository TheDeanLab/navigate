import logging

import pytest

from navigate.log_files.filters import NonPerfFilter, PerformanceFilter


@pytest.mark.parametrize(
    ("levelname", "perf_expected", "non_perf_expected"),
    [
        ("PERFORMANCE", True, False),
        ("INFO", False, True),
        ("DEBUG", False, True),
    ],
)
def test_filters_route_performance_records_by_level(
    levelname, perf_expected, non_perf_expected
):
    record = logging.makeLogRecord({"levelname": levelname, "msg": "test message"})

    assert PerformanceFilter().filter(record) is perf_expected
    assert NonPerfFilter().filter(record) is non_perf_expected
