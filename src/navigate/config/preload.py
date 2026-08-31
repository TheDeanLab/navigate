# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:
#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

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

# Standard Library Imports
from dataclasses import dataclass, field
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__.split(".")[1])
ISSUE_LOG_SEPARATOR = "-" * 30


@dataclass(frozen=True)
class PreloadChange:
    """A user-facing in-memory configuration repair."""

    path: str
    rule: str
    message: str


@dataclass(frozen=True)
class PreloadIssue:
    """A preload issue that may prevent Navigate from starting."""

    path: str
    rule: str
    message: str
    fatal: bool = False


@dataclass
class PreloadReport:
    """Structured record of in-memory preload repairs and issues."""

    changes: list[PreloadChange] = field(default_factory=list)
    issues: list[PreloadIssue] = field(default_factory=list)
    debug_changes: list[PreloadChange] = field(default_factory=list)

    @property
    def fatal_issues(self) -> list[PreloadIssue]:
        """Return fatal issues collected during preload."""
        return [issue for issue in self.issues if issue.fatal]

    @property
    def has_fatal_issues(self) -> bool:
        """Return whether preload collected any fatal issue."""
        return bool(self.fatal_issues)

    def add_change(self, path: str, rule: str, message: str) -> None:
        """Record a user-facing configuration repair."""
        self.changes.append(PreloadChange(path, rule, message))

    def add_debug_change(self, path: str, rule: str, message: str) -> None:
        """Record a non-user-facing compatibility repair."""
        self.debug_changes.append(PreloadChange(path, rule, message))

    def add_issue(
        self, path: str, rule: str, message: str, *, fatal: bool = False
    ) -> None:
        """Record a preload issue."""
        self.issues.append(PreloadIssue(path, rule, message, fatal))


class PreloadError(Exception):
    """Raised when preload cannot repair configuration safely."""

    def __init__(self, report: PreloadReport):
        self.report = report
        messages = "; ".join(issue.message for issue in report.fatal_issues)
        super().__init__(messages or "Navigate configuration preload failed.")


@dataclass
class PreloadContext:
    """Shared state passed to preload rules."""

    manager: Any
    configuration: Any
    is_synthetic: bool
    multi_positions: Optional[Any]
    report: PreloadReport


@dataclass(frozen=True)
class PreloadRule:
    """One named preload rule in a configuration domain."""

    domain: str
    name: str
    apply: Callable[[PreloadContext], None]
    stop_on_fatal: bool = False

    @property
    def rule_id(self) -> str:
        """Return a stable rule identifier for reports."""
        return f"{self.domain}.{self.name}"


def preload_configuration(
    manager,
    configuration,
    *,
    is_synthetic: bool = False,
    multi_positions: Optional[Any] = None,
) -> PreloadReport:
    """Repair in-memory configuration before Navigate starts devices."""
    from navigate.config.preload_rules import PRELOAD_RULES

    context = PreloadContext(
        manager=manager,
        configuration=configuration,
        is_synthetic=is_synthetic,
        multi_positions=multi_positions,
        report=PreloadReport(),
    )

    _run_rules(context, PRELOAD_RULES)
    _log_report(context.report)
    return context.report


def _run_rules(context: PreloadContext, rules: list[PreloadRule]) -> None:
    """Run preload rules in order and convert fatal failures into PreloadError."""
    for rule in rules:
        try:
            rule.apply(context)
        except PreloadError:
            _log_report(context.report)
            raise
        except Exception as error:
            context.report.add_issue(
                rule.domain,
                rule.rule_id,
                str(error),
                fatal=True,
            )
            _log_report(context.report)
            raise PreloadError(context.report) from error

        if rule.stop_on_fatal and context.report.has_fatal_issues:
            _log_report(context.report)
            raise PreloadError(context.report)


def _log_report(report: PreloadReport) -> None:
    """Log preload changes and issues without storing them in configuration."""
    for change in report.changes:
        logger.info("Preload repaired %s: %s", change.path, change.message)
    for change in report.debug_changes:
        logger.debug("Preload compatibility repair %s: %s", change.path, change.message)
    for issue in report.issues:
        log = logger.error if issue.fatal else logger.warning
        log(
            "%s\nPreload issue %s: %s\n%s",
            ISSUE_LOG_SEPARATOR,
            issue.path,
            issue.message,
            ISSUE_LOG_SEPARATOR,
        )
