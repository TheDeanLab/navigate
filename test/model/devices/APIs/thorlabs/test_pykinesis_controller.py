from unittest.mock import MagicMock, patch

from navigate.model.devices.APIs.thorlabs import pykinesis_controller


def build_controller():
    controller = pykinesis_controller.KinesisStage.__new__(
        pykinesis_controller.KinesisStage
    )
    controller.stage = MagicMock()
    return controller


def test_move_to_position_does_not_sleep_for_nonblocking_moves():
    controller = build_controller()
    controller.stage.get_position.return_value = 10

    with patch.object(pykinesis_controller, "sleep") as sleep_mock:
        controller.move_to_position(1.0, 2.0, wait_till_done=False)

    controller.stage.move_by.assert_called_once_with(-8, channel=1, scale=False)
    controller.stage.wait_move.assert_not_called()
    sleep_mock.assert_not_called()


def test_move_to_position_sleeps_after_blocking_wait():
    controller = build_controller()
    controller.stage.get_position.return_value = 0

    with patch.object(pykinesis_controller, "sleep") as sleep_mock:
        controller.move_to_position(1.0, 2.0, wait_till_done=True)

    controller.stage.move_by.assert_called_once_with(2, channel=1, scale=False)
    controller.stage.wait_move.assert_called_once_with(channel=1)
    sleep_mock.assert_called_once_with(pykinesis_controller.SLEEP_AFTER_WAIT)


def test_close_logs_stop_failure_and_still_closes_stage():
    controller = build_controller()
    controller.stage.stop.side_effect = RuntimeError("stop failed")

    with patch.object(pykinesis_controller.logger, "debug") as debug_mock:
        controller.close()

    debug_mock.assert_called_once()
    assert "Failed to stop KINESIS stage cleanly" in debug_mock.call_args.args[0]
    controller.stage.close.assert_called_once()
