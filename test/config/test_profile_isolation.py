"""Regression coverage for user-profile writes from tests and child processes."""

import json
import multiprocessing
import os
from pathlib import Path
import subprocess
import sys

import pytest

from navigate.config.config import get_configuration_paths, get_navigate_path
from test.profile_isolation import ProfileWriteGuard


def _save_child_profile(result_path: str) -> None:
    """Exercise profile resolution and writes in a fresh spawned interpreter."""
    paths = get_configuration_paths()
    paths[1].write_text("child experiment")
    Path(result_path).write_text(json.dumps([str(path) for path in paths]))


def test_profile_override_creates_nested_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An override is the full profile directory, not its parent."""
    profile = tmp_path / "nested" / "profile"
    monkeypatch.setenv("NAVIGATE_HOME", str(profile))
    assert get_navigate_path() == str(profile)
    assert profile.is_dir()
    assert all(path.parent == profile / "config" for path in get_configuration_paths())


def test_profile_override_is_inherited_by_spawn(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Model processes write to the same disposable profile as their parent."""
    profile = tmp_path / "child-profile"
    monkeypatch.setenv("NAVIGATE_HOME", str(profile))
    result = tmp_path / "result.json"
    process = multiprocessing.get_context("spawn").Process(
        target=_save_child_profile, args=(str(result),)
    )
    process.start()
    try:
        process.join(timeout=30)
        assert process.exitcode == 0
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=10)
    assert all(
        Path(path).parent == profile / "config"
        for path in json.loads(result.read_text())
    )
    assert (profile / "config/experiment.yml").read_text() == "child experiment"


@pytest.mark.parametrize(
    "operation", ["write", "append", "os_open", "unlink", "replace", "symlink"]
)
def test_write_guard_blocks_mutations(tmp_path: Path, operation: str) -> None:
    """Check real audit hooks against disposable sentinel files, never live ones."""
    protected = tmp_path / "protected"
    protected.mkdir()
    target = protected / "experiment.yml"
    target.write_text("original settings")
    if operation == "symlink":
        # Windows may require developer mode or elevated symlink privileges.
        probe = tmp_path / "symlink-probe"
        try:
            probe.symlink_to(target)
        except (OSError, NotImplementedError) as error:
            pytest.skip(f"Symlinks are unavailable: {error}")
        probe.unlink()
    replacement = tmp_path / "replacement.yml"
    replacement.write_text("replacement")
    script = """
import os
from pathlib import Path
import sys
from test.profile_isolation import ProfileWriteGuard
protected, replacement, operation = map(str, sys.argv[1:])
guard = ProfileWriteGuard([Path(protected)])
sys.addaudithook(guard)
target = Path(protected) / "experiment.yml"
try:
    if operation == "write": target.write_text("changed")
    elif operation == "append":
        with target.open("a") as stream: stream.write("changed")
    elif operation == "os_open": os.open(target, os.O_WRONLY | os.O_TRUNC)
    elif operation == "unlink": target.unlink()
    elif operation == "replace": os.replace(replacement, target)
    elif operation == "symlink":
        alias = Path(replacement).with_name("alias")
        alias.symlink_to(target)
        alias.write_text("changed")
except PermissionError:
    assert guard.violations
else:
    raise AssertionError("Protected write succeeded")
"""
    subprocess.run(
        [sys.executable, "-c", script, str(protected), str(replacement), operation],
        check=True,
        timeout=30,
    )
    assert target.read_text() == "original settings"


@pytest.mark.parametrize("swallow_forbidden_write", [False, True])
def test_pytest_isolates_before_collection_and_detects_swallowed_writes(
    tmp_path: Path, swallow_forbidden_write: bool
) -> None:
    """A nested session must not reuse NAVIGATE_HOME or hide rejected writes."""
    original_profile = tmp_path / "external-profile"
    original_profile.mkdir()
    sentinel = original_profile / "experiment.yml"
    sentinel.write_text("original settings")
    test_module = tmp_path / "test_nested.py"
    test_module.write_text("""
import os
from pathlib import Path
from navigate.config.config import get_configuration_paths, get_navigate_path

# This runs at collection time, before fixtures can provide any protection.
profile = Path(get_navigate_path())
assert profile != Path(os.environ["TEST_ORIGINAL_PROFILE"])
assert "navigate-pytest-" in str(profile)
Path(os.environ["TEST_PROFILE_RECORD"]).write_text(str(profile))
get_configuration_paths()[1].write_text("collection settings")

def test_save():
    get_configuration_paths()[1].write_text("shutdown settings")
    if os.environ["TEST_SWALLOW_WRITE"] == "1":
        try:
            (Path(os.environ["TEST_ORIGINAL_PROFILE"]) / "experiment.yml").write_text("bad")
        except PermissionError:
            pass
""")
    env = os.environ.copy()
    env.update(
        NAVIGATE_HOME=str(original_profile),
        TEST_ORIGINAL_PROFILE=str(original_profile),
        TEST_SWALLOW_WRITE=str(int(swallow_forbidden_write)),
        TEST_PROFILE_RECORD=str(tmp_path / "profile-path.txt"),
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import os, sys, pytest; original = os.environ['NAVIGATE_HOME']; "
            "code = pytest.main(sys.argv[1:]); "
            "assert os.environ['NAVIGATE_HOME'] == original; sys.exit(code)",
            "-p",
            "test.conftest",
            "-p",
            "no:cov",
            "-o",
            "addopts=",
            "--confcutdir",
            str(tmp_path),
            str(test_module),
            "-q",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == int(swallow_forbidden_write), (
        result.stdout + result.stderr
    )
    if swallow_forbidden_write:
        assert "Blocked writes to protected profiles" in result.stdout
    assert sentinel.read_text() == "original settings"
    assert not Path((tmp_path / "profile-path.txt").read_text()).exists()
