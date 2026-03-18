from types import SimpleNamespace

import numpy as np


class _DummyVar:
    def trace_add(self, *_args):
        return None


class _DummyWidget(dict):
    def bind(self, *_args, **_kwargs):
        return None


class _DummyInput:
    def __init__(self, value=None):
        self.value = value
        self.variable = _DummyVar()
        self.widget = _DummyWidget()

    def set(self, value):
        self.value = value

    def get(self):
        return self.value

    def get_variable(self):
        return self.variable


class _DummyAxis:
    def __init__(self):
        self.lines = []
        self.title = None
        self.xlabel = None
        self.ylabel = None

    def clear(self):
        self.lines = []

    def plot(self, x, y, **kwargs):
        self.lines.append((np.asarray(x), np.asarray(y), kwargs))

    def set_title(self, value):
        self.title = value

    def set_xlabel(self, value):
        self.xlabel = value

    def set_ylabel(self, value):
        self.ylabel = value

    def legend(self):
        return None


class _DummyCanvas:
    def draw_idle(self):
        return None

    def get_tk_widget(self):
        return object()


class _DummyNotebook:
    def bind(self, *_args, **_kwargs):
        return None

    def select(self):
        return "waveforms"

    def tab(self, _tab_id, option):
        assert option == "text"
        return "Waveforms"


def test_waveform_tab_uses_updated_remote_focus_waveform(monkeypatch):
    from navigate.controller.sub_controllers.waveform_tab import WaveformTabController

    def fake_initialize_plots(self):
        self.view.plot_etl = _DummyAxis()
        self.view.plot_galvo = _DummyAxis()

    monkeypatch.setattr(
        WaveformTabController,
        "initialize_plots",
        fake_initialize_plots,
    )

    view = SimpleNamespace(
        canvas=_DummyCanvas(),
        fig=SimpleNamespace(tight_layout=lambda: None),
        is_docked=True,
        master=_DummyNotebook(),
        waveform_settings=SimpleNamespace(
            inputs={
                "sample_rate": _DummyInput(),
                "waveform_template": _DummyInput(),
            }
        ),
    )
    parent_controller = SimpleNamespace(
        configuration={
            "configuration": {"microscopes": {"TestScope": {"daq": {"sample_rate": 1000}}}},
            "experiment": {
                "MicroscopeState": {
                    "microscope_name": "TestScope",
                    "waveform_template": "Default",
                }
            },
            "waveform_templates": {"Default": {"repeat": 1, "expand": 1}},
        },
        event_listeners={},
    )

    controller = WaveformTabController(view, parent_controller)
    dithered_remote_focus = np.array([0.0, 0.2, -0.1, 0.3], dtype=float)
    waveform_dict = {
        "remote_focus_waveform": {"channel_1": dithered_remote_focus},
        "camera_waveform": {"channel_1": np.array([0.0, 1.0, 0.0, 1.0], dtype=float)},
        "galvo_waveform": [
            {"channel_1": np.array([0.5, 0.6, 0.7, 0.8], dtype=float)}
        ],
    }

    controller.update_waveforms(waveform_dict)

    etl_time, etl_signal, etl_kwargs = controller.view.plot_etl.lines[0]
    np.testing.assert_array_equal(
        etl_time, np.arange(len(dithered_remote_focus)) / controller.sample_rate
    )
    np.testing.assert_array_equal(etl_signal, dithered_remote_focus)
    assert etl_kwargs["label"] == "CH1"
    assert controller.view.plot_etl.title == "Remote Focus Waveform"
