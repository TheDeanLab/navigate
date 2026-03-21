from types import SimpleNamespace
from unittest.mock import Mock

import navigate.tools.tk_thread_guard as guard


def test_install_skips_missing_and_noncallable_tk_methods(monkeypatch):
    class PartialTkApp:
        call = "not-callable"

        def eval(self, *args, **kwargs):
            return ("eval", args, kwargs)

    root = SimpleNamespace(tk=PartialTkApp())
    logger = Mock()

    monkeypatch.setattr(guard, "_guard_disabled_by_environment", lambda: False)

    assert guard.install_tk_thread_guard(root, logger=logger) is True
    assert root.tk.eval("expr")[0] == "eval"
    logger.info.assert_called()
