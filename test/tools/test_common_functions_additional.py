from types import ModuleType, SimpleNamespace

import pytest

import navigate.tools.common_functions as common_functions


def test_load_module_from_file_returns_none_on_module_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_module_not_found(_module: ModuleType) -> None:
        raise ModuleNotFoundError("missing dependency")

    monkeypatch.setattr(
        common_functions.importlib.util,
        "spec_from_file_location",
        lambda module_name, file_path: SimpleNamespace(
            loader=SimpleNamespace(exec_module=raise_module_not_found)
        ),
    )
    monkeypatch.setattr(
        common_functions.importlib.util,
        "module_from_spec",
        lambda spec: ModuleType("fake_module"),
    )

    assert common_functions.load_module_from_file("fake_module", "/tmp/fake.py") is None


def test_load_module_from_file_returns_none_on_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_import_error(_module: ModuleType) -> None:
        raise ImportError("DLL load failed while importing cupy")

    monkeypatch.setattr(
        common_functions.importlib.util,
        "spec_from_file_location",
        lambda module_name, file_path: SimpleNamespace(
            loader=SimpleNamespace(exec_module=raise_import_error)
        ),
    )
    monkeypatch.setattr(
        common_functions.importlib.util,
        "module_from_spec",
        lambda spec: ModuleType("fake_module"),
    )

    assert common_functions.load_module_from_file("fake_module", "/tmp/fake.py") is None


def test_load_module_from_file_returns_none_without_module_spec(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        common_functions.importlib.util,
        "spec_from_file_location",
        lambda module_name, file_path: None,
    )

    assert common_functions.load_module_from_file("fake_module", "/tmp/fake.py") is None


def test_load_module_from_file_returns_none_without_module_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        common_functions.importlib.util,
        "spec_from_file_location",
        lambda module_name, file_path: SimpleNamespace(loader=None),
    )

    assert common_functions.load_module_from_file("fake_module", "/tmp/fake.py") is None


def test_load_param_from_module_success(monkeypatch):
    module = SimpleNamespace(target=123)
    monkeypatch.setattr(
        common_functions.importlib, "import_module", lambda module_name: module
    )

    assert common_functions.load_param_from_module("pkg.module", "target") == 123


def test_load_param_from_module_returns_none_for_missing_module(monkeypatch):
    def raise_module_not_found(module_name):
        raise ModuleNotFoundError(module_name)

    monkeypatch.setattr(
        common_functions.importlib, "import_module", raise_module_not_found
    )

    assert common_functions.load_param_from_module("missing.module", "target") is None


def test_decode_bytes_handles_memoryview_and_non_bytes():
    assert common_functions.decode_bytes(memoryview(b"hello")) == "hello"
    assert common_functions.decode_bytes("not-bytes") == ""


def test_decode_bytes_returns_empty_string_on_decode_error():
    class BadBytes(bytes):
        def decode(self, errors="ignore"):
            raise RuntimeError("decode failure")

    assert common_functions.decode_bytes(BadBytes(b"boom")) == ""


def test_variable_with_lock_acquires_and_releases_lock():
    variable = common_functions.VariableWithLock(list)

    assert variable.value == []
    assert variable.lock.locked() is False

    with variable as locked_variable:
        assert locked_variable is variable
        assert variable.lock.locked() is True
        locked_variable.value.append("item")

    assert variable.lock.locked() is False
    assert variable.value == ["item"]
