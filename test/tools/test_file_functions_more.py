from types import SimpleNamespace

from navigate.tools import file_functions


def test_get_ram_info_returns_total_and_available(monkeypatch):
    monkeypatch.setattr(
        file_functions.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=1024, available=256),
    )

    assert file_functions.get_ram_info() == (1024, 256)
