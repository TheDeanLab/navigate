# Windows Constraints and Dependency Canary Design

## Goal

Keep the supported Windows Python 3.9 and 3.10 environments reproducible while
retaining early warning when unconstrained dependency updates become
incompatible.

## Constraint snapshots

Add `constraints/windows-py39.txt` and `constraints/windows-py310.txt`. Each
file records every dependency resolved by the corresponding successful Windows
CI job, including dependencies already present in the runner environment, but
excluding the editable `navigate-micro` project itself and pip. These files are
pip constraints: they control versions selected during installation without
moving transitive dependencies into `pyproject.toml`.

The file headers identify the source workflow run and Python version. A future
refresh should resolve the full `.[dev]` environment on the matching Windows
Python version, run the test suite, and replace the snapshot only after that
environment is green.

## Required CI

The required Windows test matrix continues to cover Python 3.9 and 3.10. Each
matrix entry:

- uses its matching constraint file;
- installs the editable development environment with
  `pip install -c constraints/windows-<python-tag>.txt -e ".[dev]"`; and
- uses setup-python's pip cache keyed by the matching constraint file.

Checkout, setup-python, and Codecov use their current supported major versions.

## Unconstrained dependency canary

The existing workflow gains one weekly scheduled Windows Python 3.10 job. It
installs `.[dev]` without a constraint and runs the same test suite. The job
exists only for scheduled events, so a failure remains visible as an early
warning but cannot become a required pull-request check. Required matrix jobs
do not run for scheduled events.

## Documentation

Windows source and developer installation examples use the constraint matching
the active Python version. Stable PyPI installation remains unconstrained
because those users install a released distribution rather than reproduce a
repository-tested source environment.

## Verification

Validate that both snapshots contain unique, sorted, exact requirements; parse
the workflow; build the Sphinx documentation with warnings treated as errors;
run repository policy checks; and confirm both constrained Windows jobs pass
after pushing the branch.
