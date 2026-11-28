"""Protect user profiles and shipped configuration during pytest sessions."""

from __future__ import annotations

import builtins
import functools
import io
import _io
import os
from pathlib import Path
import sys
from typing import Any, Callable, Iterable

import pytest


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
        self._patches = pytest.MonkeyPatch()

    def install(self) -> None:
        """Install write checks without breaking tracing on older CPython.

        CPython before 3.12 holds a process-wide trace-installation flag while
        running audit hooks. A thread switch inside a Python hook can make
        another thread's coverage/debugger startup fail before its target runs.
        Use reversible filesystem API wrappers on those interpreters instead.
        """
        # The open audit event omits dir_fd, so wrappers are also needed on
        # newer runtimes to resolve directory-relative writes correctly.
        self._install_wrappers()
        if sys.implementation.name != "cpython" or sys.version_info >= (3, 12):
            sys.addaudithook(self)

    def close(self) -> None:
        """Disable checks and restore any wrapped filesystem functions."""
        self.enabled = False
        self._patches.undo()

    def _install_wrappers(self) -> None:
        """Guard Python file operations without registering an audit hook."""

        def patch(module: Any, name: str, wrapper: Callable[..., Any]) -> None:
            original = getattr(module, name)
            self._patches.setattr(module, name, functools.wraps(original)(wrapper))
            # Python 3.9/3.10 pathlib caches file functions in an accessor.
            # Match by identity: its open function is os.open on 3.9 and
            # io.open on 3.10, with different call signatures.
            accessor = getattr(Path, "_accessor", None)
            if accessor is not None:
                for alias in (name, "link_to") if name == "link" else (name,):
                    if getattr(accessor, alias, None) is original:
                        self._patches.setattr(accessor, alias, wrapper)
            if module is os:
                for attribute in (
                    "supports_dir_fd",
                    "supports_fd",
                    "supports_follow_symlinks",
                ):
                    capabilities = getattr(os, attribute)
                    if original in capabilities:
                        # Preserve capability queries used by pathlib/shutil.
                        self._patches.setattr(os, attribute, capabilities | {wrapper})

        def wrap_open(original: Callable[..., Any]) -> Callable[..., Any]:
            def open_file(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
                self("open", (file, mode, 0))
                return original(file, mode, *args, **kwargs)

            return open_file

        for module in (builtins, io, _io):
            patch(module, "open", wrap_open(module.open))

        original_file_io = io.FileIO
        guard = self

        class GuardedFileIO(original_file_io):
            def __init__(
                self, file: Any, mode: str = "r", *args: Any, **kwargs: Any
            ) -> None:
                guard("open", (file, mode, 0))
                super().__init__(file, mode, *args, **kwargs)

        self._patches.setattr(io, "FileIO", GuardedFileIO)
        self._patches.setattr(_io, "FileIO", GuardedFileIO)
        original_os_open = os.open

        def open_descriptor(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
            if flags & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            ):
                self._check(path, kwargs.get("dir_fd"))
            return original_os_open(path, flags, *args, **kwargs)

        patch(os, "open", open_descriptor)

        def wrap_path(
            original: Callable[..., Any], ancestors: bool
        ) -> Callable[..., Any]:
            def mutate(path: Any, *args: Any, **kwargs: Any) -> Any:
                self._check(path, kwargs.get("dir_fd"), ancestors=ancestors)
                return original(path, *args, **kwargs)

            return mutate

        for name in (
            "remove",
            "unlink",
            "rmdir",
            "mkdir",
            "chmod",
            "lchmod",
            "chown",
            "lchown",
            "utime",
            "truncate",
        ):
            if hasattr(os, name):
                patch(
                    os,
                    name,
                    wrap_path(getattr(os, name), name in ("remove", "unlink", "rmdir")),
                )

        def wrap_pair(original: Callable[..., Any], rename: bool) -> Callable[..., Any]:
            def mutate(src: Any, dst: Any, *args: Any, **kwargs: Any) -> Any:
                if rename:
                    self._check(src, kwargs.get("src_dir_fd"), ancestors=True)
                self._check(
                    dst,
                    kwargs.get("dst_dir_fd", kwargs.get("dir_fd")),
                    ancestors=rename,
                )
                return original(src, dst, *args, **kwargs)

            return mutate

        for name in ("rename", "replace", "symlink", "link"):
            if hasattr(os, name):
                patch(
                    os,
                    name,
                    wrap_pair(getattr(os, name), name in ("rename", "replace")),
                )

    def _check(
        self, path: Any, dir_fd: int | None = None, *, ancestors: bool = False
    ) -> None:
        if not self.enabled or not isinstance(path, (str, bytes, os.PathLike)):
            return
        path = os.fsdecode(path)
        # Pytest's logging handler opens the null device. Windows Python 3.9
        # cannot resolve its device-namespace path with Path.resolve().
        if os.path.normcase(os.path.abspath(path)).rstrip("\\/") == os.path.normcase(
            os.path.abspath(os.devnull)
        ).rstrip("\\/"):
            return
        path = Path(path)
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
