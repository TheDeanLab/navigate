from types import SimpleNamespace
from unittest.mock import Mock

import navigate.tools.tk_thread_guard as guard


def _build_root_with_tk_methods():
    class DummyTkApp:
        def call(self, *args, **kwargs):
            return ("call", args, kwargs)

        def eval(self, *args, **kwargs):
            return ("eval", args, kwargs)

        def evalfile(self, *args, **kwargs):
            return ("evalfile", args, kwargs)

        def setvar(self, *args, **kwargs):
            return ("setvar", args, kwargs)

        def getvar(self, *args, **kwargs):
            return ("getvar", args, kwargs)

        def globalsetvar(self, *args, **kwargs):
            return ("globalsetvar", args, kwargs)

        def globalgetvar(self, *args, **kwargs):
            return ("globalgetvar", args, kwargs)

    return SimpleNamespace(tk=DummyTkApp())


def test_guard_disabled_by_explicit_disable_env(monkeypatch):
    monkeypatch.setenv("NAVIGATE_DISABLE_TK_THREAD_GUARD", "ON")
    monkeypatch.delenv("NAVIGATE_ENABLE_TK_THREAD_GUARD_IN_TESTS", raising=False)
    assert guard._guard_disabled_by_environment() is True


def test_guard_disabled_under_pytest_by_default(monkeypatch):
    monkeypatch.delenv("NAVIGATE_DISABLE_TK_THREAD_GUARD", raising=False)
    monkeypatch.delenv("NAVIGATE_ENABLE_TK_THREAD_GUARD_IN_TESTS", raising=False)
    assert guard._guard_disabled_by_environment() is True


def test_guard_can_be_forced_under_pytest(monkeypatch):
    monkeypatch.delenv("NAVIGATE_DISABLE_TK_THREAD_GUARD", raising=False)
    monkeypatch.setenv("NAVIGATE_ENABLE_TK_THREAD_GUARD_IN_TESTS", "true")
    assert guard._guard_disabled_by_environment() is False


def test_install_returns_false_when_environment_disables_guard(monkeypatch):
    logger = Mock()
    root = _build_root_with_tk_methods()

    monkeypatch.setattr(guard, "_guard_disabled_by_environment", lambda: True)
    assert guard.install_tk_thread_guard(root, logger=logger) is False
    logger.info.assert_called_once()


def test_install_wraps_methods_and_logs_off_main_thread(monkeypatch):
    logger = Mock()
    root = _build_root_with_tk_methods()

    current_ident = {"value": 101}
    monkeypatch.setattr(guard, "_guard_disabled_by_environment", lambda: False)
    monkeypatch.setattr(guard.threading, "get_ident", lambda: current_ident["value"])
    monkeypatch.setattr(
        guard.threading, "current_thread", lambda: SimpleNamespace(name="worker")
    )
    monkeypatch.setattr(
        guard.traceback, "format_stack", lambda limit=8: ["frame_a\n", "frame_b\n"]
    )

    installed = guard.install_tk_thread_guard(root, logger=logger)
    assert installed is True
    assert getattr(type(root.tk), "_navigate_tk_guard_installed") is True

    # Same-thread invocation should pass through without warning.
    result_same_thread = root.tk.call("same-thread")
    assert result_same_thread[0] == "call"

    # Simulate off-main-thread call and verify warning path.
    current_ident["value"] = 202
    result_off_thread = root.tk.call("off-thread")
    assert result_off_thread[0] == "call"
    assert logger.warning.call_count >= 1

    # Idempotent: second install on same class should be a no-op.
    assert guard.install_tk_thread_guard(root, logger=logger) is False


def test_install_uses_default_logger_when_none(monkeypatch):
    root = _build_root_with_tk_methods()
    default_logger = Mock()
    logging_module = Mock()
    logging_module.getLogger.return_value = default_logger

    monkeypatch.setattr(guard, "_guard_disabled_by_environment", lambda: False)
    monkeypatch.setattr(guard, "logging", logging_module)

    assert guard.install_tk_thread_guard(root, logger=None) is True
    default_logger.info.assert_called()
