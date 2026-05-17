from unittest.mock import MagicMock, patch

import navigate.model.devices.stage.thorlabs as thorlabs
from navigate.model.devices.stage.thorlabs import KINESISStage


def build_stage(controller=None):
    configuration = {
        "configuration": {
            "microscopes": {
                "TestScope": {
                    "stage": {
                        "hardware": {
                            "type": "KINESIS",
                            "serial_number": "/dev/ttyUSB1",
                            "axes": ["f"],
                            "axes_mapping": [1],
                            "steps_per_um": 2000.0,
                        },
                        "f_min": 0,
                        "f_max": 25000,
                    }
                }
            }
        }
    }
    return KINESISStage(
        microscope_name="TestScope",
        device_connection=controller or MagicMock(),
        configuration=configuration,
    )


def test_del_logs_cleanup_failures_and_attempts_close():
    controller = MagicMock()
    controller.stop.side_effect = RuntimeError("stop failed")
    controller.close.side_effect = RuntimeError("close failed")
    stage = build_stage(controller)

    with patch.object(thorlabs.logger, "debug") as debug_mock:
        stage.__del__()

    assert debug_mock.call_count == 2
    controller.stop.assert_called_once()
    controller.close.assert_called_once()
    stage.kinesis_controller = None


def test_del_returns_when_controller_was_not_initialized():
    stage = KINESISStage.__new__(KINESISStage)

    with patch.object(thorlabs.logger, "debug") as debug_mock:
        stage.__del__()

    debug_mock.assert_not_called()


def test_report_position_logs_failure_and_returns_cached_position():
    controller = MagicMock()
    controller.get_current_position.side_effect = RuntimeError("read failed")
    stage = build_stage(controller)

    with patch.object(thorlabs.logger, "debug") as debug_mock:
        position = stage.report_position()

    assert position == {"f_pos": 0}
    debug_mock.assert_called_once()
    assert "Error while reporting KINESISStage position" in debug_mock.call_args.args[0]
    stage.kinesis_controller = None
