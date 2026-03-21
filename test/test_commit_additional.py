import subprocess
from unittest.mock import MagicMock

from navigate._commit import get_git_revision_hash, get_version_from_file


def test_get_git_revision_hash_restores_working_directory_on_success(monkeypatch):
    chdir = MagicMock()
    monkeypatch.setattr("navigate._commit.os.getcwd", lambda: "/original")
    monkeypatch.setattr("navigate._commit.os.chdir", chdir)
    monkeypatch.setattr(
        "navigate._commit.subprocess.check_output",
        MagicMock(side_effect=[b"true", b"abc123"]),
    )

    assert get_git_revision_hash() == "abc123"
    assert chdir.call_args_list[-1].args[0] == "/original"


def test_get_git_revision_hash_returns_none_when_git_is_unavailable(monkeypatch):
    chdir = MagicMock()
    monkeypatch.setattr("navigate._commit.os.getcwd", lambda: "/original")
    monkeypatch.setattr("navigate._commit.os.chdir", chdir)
    monkeypatch.setattr(
        "navigate._commit.subprocess.check_output",
        MagicMock(side_effect=FileNotFoundError),
    )

    assert get_git_revision_hash() is None
    assert chdir.call_args_list[-1].args[0] == "/original"


def test_get_git_revision_hash_returns_none_when_repo_check_is_false(monkeypatch):
    check_output = MagicMock(return_value=b"")
    monkeypatch.setattr("navigate._commit.subprocess.check_output", check_output)

    assert get_git_revision_hash() is None
    check_output.assert_called_once_with(
        ["git", "rev-parse", "--is-inside-work-tree"], stderr=subprocess.DEVNULL
    )


def test_get_version_from_file_reads_custom_version_file(tmp_path, monkeypatch):
    version_file = tmp_path / "CUSTOM_VERSION"
    version_file.write_text("9.9.9\n")

    monkeypatch.setattr(
        "navigate._commit.os.path.abspath", lambda path: str(tmp_path / "module.py")
    )

    assert get_version_from_file("CUSTOM_VERSION") == "9.9.9"
