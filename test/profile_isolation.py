"""Protect user profiles and shipped configuration during pytest sessions."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable


class ProfileWriteGuard:
    """Reject Python filesystem mutations of protected profile paths.

    Parameters
    ----------
    paths : iterable of Path
        Directories or files that tests may read but must never modify.
    """

    def __init__(self, paths: Iterable[Path]) -> None:
        self.paths = tuple(path.resolve() for path in paths)
        self.enabled = True
        self.violations: list[str] = []

    def _check(
        self, path: Any, dir_fd: int | None = None, *, ancestors: bool = False
    ) -> None:
        if not isinstance(path, (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(path))
        if not path.is_absolute() and dir_fd not in (None, -1):
            # Linux exposes directory descriptors here. Fail closed elsewhere
            # rather than allowing a relative write whose destination is unknown.
            descriptor = Path(f"/proc/self/fd/{dir_fd}")
            if not descriptor.exists():
                message = f"Cannot verify test write relative to directory fd {dir_fd}"
                self.violations.append(message)
                raise PermissionError(message)
            path = descriptor / path
        path = path.resolve()
        if any(
            path == root or root in path.parents or (ancestors and path in root.parents)
            for root in self.paths
        ):
            message = f"Tests must not modify protected profile/configuration: {path}"
            self.violations.append(message)
            raise PermissionError(message)

    def __call__(self, event: str, args: tuple[Any, ...]) -> None:
        """Check filesystem audit events before their mutations take place."""
        if not self.enabled:
            return
        if event == "open":
            path, mode, flags = args
            if (mode and any(flag in mode for flag in "wax+")) or (
                flags
                & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ):
                self._check(path)
        elif event in ("os.remove", "os.rmdir"):
            self._check(args[0], args[1], ancestors=True)
        elif event in ("os.mkdir", "os.chmod", "os.chown", "os.utime"):
            self._check(args[0], args[-1])
        elif event == "os.rename":
            self._check(args[0], args[2], ancestors=True)
            self._check(args[1], args[3], ancestors=True)
        elif event in ("os.symlink", "os.link"):
            self._check(args[1], args[-1])
        elif event == "os.truncate":
            self._check(args[0])
