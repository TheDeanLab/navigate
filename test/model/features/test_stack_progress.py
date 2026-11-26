"""Animation must not alter trajectories, camera processing or stage I/O."""

from queue import Queue
from unittest.mock import Mock

import pytest

from navigate.model.features.common_features import (
    ASIZStackAcquisition,
    ZStackAcquisition,
)
from navigate.model.stack_acquisition import freeze_relative_stack
from test.model.test_relative_stack_acquisition import relative_model


@pytest.mark.parametrize("alternate_axes", [False, True])
@pytest.mark.parametrize("feature_type", [ZStackAcquisition, ASIZStackAcquisition])
@pytest.mark.parametrize("relative", [False, True])
@pytest.mark.parametrize("cycling", ["per_stack", "per_z"])
@pytest.mark.parametrize("flipped", [False, True])
@pytest.mark.parametrize("multiposition", [False, True])
def test_received_planes_match_plan_with_no_extra_stage_queries_or_moves(
    feature_type, relative, cycling, flipped, multiposition, alternate_axes, monkeypatch
):
    monkeypatch.setattr(
        "navigate.model.features.common_features.time.sleep", lambda _: None
    )
    clock = [0.0]
    monkeypatch.setattr("navigate.tools.stack_progress.monotonic", lambda: clock[0])
    observations = []
    for enabled in (False, True):
        model, state, _, moves = relative_model(
            cycling=cycling,
            flipped=flipped,
            multiposition=multiposition,
            alternate_axes=alternate_axes,
        )
        state["timepoints"] = 2
        state["stack_position_mode"] = "relative" if relative else "absolute"
        state.update(
            relative_focus_ramp=True, relative_start_focus=-5, relative_end_focus=5
        )
        if not relative:
            state["step_size"] = -0.7 if flipped else 0.7
        if relative:
            model._relative_stack_plan = freeze_relative_stack(model)
        model._stack_progress_token = (9, "scope")
        output = model.stack_progress_queue = Queue(1) if enabled else None
        feature = feature_type(model)
        feature.image_writer = Mock()
        n = state["number_z_steps"]
        references = (
            [(3000, 90), (4500, 100)]
            if multiposition
            else ([(1000, 50)] if relative else [(2000, 70)])
        )
        if alternate_axes:
            references = (
                [(30, 150), (40, 175)]
                if multiposition
                else ([(20, 100)] if relative else [(2000, 70)])
            )
        expected = []
        for t in range(2):
            for p, (z, f) in enumerate(references):
                order = (
                    [(c, i) for c in range(2) for i in range(n)]
                    if cycling == "per_stack"
                    else [(c, i) for i in range(n) for c in range(2)]
                )
                for c, i in order:
                    expected.append(
                        (
                            state["start_position"] + z + i * state["step_size"],
                            (state["start_focus"] - 3)
                            + f
                            + i * (state["end_focus"] - state["start_focus"]) / n
                            + [3, -1.5][c],
                            i + 1,
                            p + 1,
                            t + 1,
                            ["channel_1", "channel_2"][c],
                        )
                    )
        received = 0
        for _ in range(2):
            feature.pre_signal_func()
            # Signal can be ahead of data. Snapshot coordinates must not come
            # from these mutable current-position/channel indices.
            for _ in range(n * 2 * len(references)):
                feature.signal_func()
                model.frame_id += 1
                if feature.signal_end():
                    break
            before_reads = model.get_stage_position.call_count
            feature.pre_data_func()
            remaining = n * 2 * len(references)
            for size in [1, 3, 2, remaining]:
                size = min(size, remaining)
                if size == 0:
                    break
                ids = [(99 + i) % 100 for i in range(size)]
                clock[0] += 0.2
                feature.in_data_func(ids)
                received += size
                remaining -= size
                feature.image_writer.save_image.assert_called_with(ids)
                if enabled:
                    snapshot = output.get_nowait()
                    assert snapshot.completed == received
                    assert snapshot.total == len(expected)
                    assert (snapshot.z, snapshot.focus) == pytest.approx(
                        expected[received - 1][:2]
                    )
                    assert (
                        snapshot.plane,
                        snapshot.position,
                        snapshot.timepoint,
                        snapshot.channel,
                    ) == expected[received - 1][2:]
            assert feature.end_data_func()
            assert model.get_stage_position.call_count == before_reads
        observations.append(
            (moves, model.get_stage_position.call_count, model.stop_stage.call_count)
        )
    assert observations[0] == observations[1]


def test_custom_features_do_not_publish_standard_stack_animation():
    model, _, _, _ = relative_model()
    model.imaging_mode = "customized"
    model.stack_progress_queue = Queue(1)
    model._stack_progress_token = (1, "scope")
    feature = ZStackAcquisition(model)
    feature.pre_signal_func()
    feature.pre_data_func()
    feature.in_data_func([0, 1])
    assert model.stack_progress_queue.empty()


def test_progress_transport_failure_does_not_interrupt_saving():
    model, _, _, _ = relative_model()
    model.stack_progress_queue = Mock()
    model.stack_progress_queue.put_nowait.side_effect = OSError("closed")
    model._stack_progress_token = (1, "scope")
    feature = ZStackAcquisition(model)
    feature.image_writer = Mock()
    feature.pre_signal_func()
    feature.pre_data_func()
    feature.in_data_func([0, 1])
    feature.in_data_func([2])
    assert feature.received_frames == 3
    assert feature.image_writer.save_image.call_count == 2
    assert feature._stack_progress is None
