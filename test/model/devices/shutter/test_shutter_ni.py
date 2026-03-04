# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.
#
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

import importlib
import sys
import types
from unittest.mock import MagicMock, patch, call

import pytest


MODULE_PATH = "navigate.model.devices.shutter.ni"
NIDAQMX_MODULE_PATH = "nidaqmx"
NIDAQMX_CONSTANTS_PATH = "nidaqmx.constants"


class _FakeDaqError(Exception):
    """Local stand-in for nidaqmx.errors.DaqError."""


class _FakeLineGrouping:
    CHAN_FOR_ALL_LINES = "chan_for_all_lines"


@pytest.fixture
def ni_module(monkeypatch):
    task_factory = MagicMock(name="TaskFactory")

    nidaqmx_module = types.ModuleType(NIDAQMX_MODULE_PATH)
    nidaqmx_module.Task = task_factory
    nidaqmx_module.errors = types.SimpleNamespace(DaqError=_FakeDaqError)

    constants_module = types.ModuleType(NIDAQMX_CONSTANTS_PATH)
    constants_module.LineGrouping = _FakeLineGrouping

    monkeypatch.setitem(sys.modules, NIDAQMX_MODULE_PATH, nidaqmx_module)
    monkeypatch.setitem(sys.modules, NIDAQMX_CONSTANTS_PATH, constants_module)

    sys.modules.pop(MODULE_PATH, None)
    module = importlib.import_module(MODULE_PATH)
    module = importlib.reload(module)
    return module, task_factory


@pytest.fixture
def shutter_config():
    return {
        "configuration": {
            "microscopes": {
                "TestScope": {
                    "shutter": {"hardware": {"channel": "Dev1/port0/line0"}}
                }
            }
        }
    }


def _build_task_mock():
    task = MagicMock(name="NITask")
    task.do_channels = MagicMock()
    return task


def test_init_open_close_and_state(ni_module, shutter_config):
    module, task_factory = ni_module
    task = _build_task_mock()
    task_factory.return_value = task

    shutter = module.NIShutter("TestScope", None, shutter_config)

    task.do_channels.add_do_chan.assert_called_once_with(
        "Dev1/port0/line0", line_grouping=module.LineGrouping.CHAN_FOR_ALL_LINES
    )
    assert task.write.call_args_list == [call(True, auto_start=True)]
    assert shutter.state is True

    shutter.close_shutter()
    shutter.open_shutter()
    assert task.write.call_args_list == [
        call(True, auto_start=True),
        call(False, auto_start=True),
        call(True, auto_start=True),
    ]
    assert shutter.state is True

    shutter.shutter_task = None


def test_open_shutter_handles_daq_error(ni_module, shutter_config, capsys):
    module, task_factory = ni_module
    task = _build_task_mock()
    task_factory.return_value = task
    shutter = module.NIShutter("TestScope", None, shutter_config)

    task.write.reset_mock()
    task.write.side_effect = _FakeDaqError("open failure")
    shutter.open_shutter()

    out = capsys.readouterr().out
    assert "shutter did not open" in out
    assert shutter.state is True
    task.write.assert_called_once_with(True, auto_start=True)

    shutter.shutter_task = None


def test_close_shutter_handles_daq_error(ni_module, shutter_config, capsys):
    module, task_factory = ni_module
    task = _build_task_mock()
    task_factory.return_value = task
    shutter = module.NIShutter("TestScope", None, shutter_config)

    task.write.reset_mock()
    task.write.side_effect = _FakeDaqError("close failure")
    shutter.close_shutter()

    out = capsys.readouterr().out
    assert "shutter did not close" in out
    assert shutter.state is False
    task.write.assert_called_once_with(False, auto_start=True)

    shutter.shutter_task = None


def test_del_stops_and_closes_task(ni_module, shutter_config):
    module, task_factory = ni_module
    task = _build_task_mock()
    task_factory.return_value = task
    shutter = module.NIShutter("TestScope", None, shutter_config)

    task.stop.reset_mock()
    task.close.reset_mock()
    shutter.__del__()

    task.stop.assert_called_once_with()
    task.close.assert_called_once_with()
    shutter.shutter_task = None


def test_del_handles_task_stop_exception(ni_module, shutter_config):
    module, task_factory = ni_module
    task = _build_task_mock()
    task_factory.return_value = task
    shutter = module.NIShutter("TestScope", None, shutter_config)
    task.stop.side_effect = RuntimeError("stop failed")

    with patch.object(module.logger, "exception") as mock_exception:
        shutter.__del__()

    mock_exception.assert_called_once()
    task.close.assert_not_called()
    shutter.shutter_task = None


def test_del_without_task_is_noop(ni_module):
    module, _ = ni_module
    shutter = object.__new__(module.NIShutter)
    shutter.shutter_task = None

    shutter.__del__()
