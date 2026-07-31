# Python 3.11 and 3.12 Windows CI Design

## Goal

Extend the Windows compatibility policy established in PR #1179:

- retain Python 3.9 and 3.10 as required lanes;
- add Python 3.11 as a required lane with a reproducible constraint snapshot;
- add Python 3.12 as a separately labeled, non-blocking experimental lane; and
- retain exactly one scheduled, unconstrained latest-dependencies canary.

Python 3.12 is eligible for the experimental lane only if the complete Windows
dependency graph resolves, including the vendor-facing packages.

## Dependency eligibility

Resolve `pyproject.toml` with the `dev` extra for 64-bit Windows independently
for Python 3.11 and 3.12. The initial resolution check must include, at minimum:

- `PIPython`;
- `nidaqmx`, `nitypes`, and `hightime`;
- `pyserial` and `pyusb`; and
- the compiled scientific and imaging dependencies required by the project.

The approved pre-implementation check resolved the full graph for both Python
versions. Python 3.12 therefore qualifies for the experimental lane. A real
Windows installation remains the authoritative check for wheel availability
and installation behavior.

## Constraint snapshots

Add:

- `constraints/windows-py311.txt`; and
- `constraints/windows-py312.txt`.

Generate each snapshot from a complete Windows-targeted `.[dev]` resolution,
using normalized distribution names, exact versions, deterministic ordering,
and no editable `navigate-micro` entry. Include a runner-provided
`setuptools` version only when it is present in the target environment; do not
invent a main-environment pin for an isolated build dependency.

The first CI run is provisional provenance. After installation, compare the
actual Windows package set with the snapshot. Update the snapshot and its
header to cite the corresponding workflow job before finalizing the PR. Python
3.11 must have a green install and test run. Python 3.12 must install the full
dependency graph; its tests may fail while the lane remains experimental, but
any failure must be reported rather than hidden.

## Required Python 3.11 lane

Add Python 3.11 to the existing required Windows matrix with tag `py311`. It
uses the same workflow path as Python 3.9 and 3.10:

- setup-python pip caching keyed by `constraints/windows-py311.txt`;
- `pip install -c constraints/windows-py311.txt -e ".[dev]"`;
- the complete pytest suite with plugin integration enabled;
- a distinct coverage file and Codecov flag; and
- the existing failure-only Windows process diagnostics.

The Python 3.9 and 3.10 lanes remain unchanged and required.

## Experimental Python 3.12 lane

Add one separate Windows Python 3.12 job named as experimental and set
`continue-on-error: true` at the job level. Keeping it outside the required
matrix makes its status unambiguous and prevents it from changing the required
check contract.

The job uses `constraints/windows-py312.txt`, setup-python caching, and the
same editable `.[dev]` installation. It runs the complete pytest suite with
plugin integration enabled. It does not upload Codecov results; the purpose is
compatibility discovery, while required coverage remains owned by the required
matrix.

The existing scheduled `latest-dependencies` job remains the only
unconstrained canary. It continues to run on Windows Python 3.10 only for
scheduled events. The experimental 3.12 lane runs on pull requests, pushes to
`develop`, and manual dispatches, but not on scheduled events.

## Package metadata and documentation

Once the required 3.11 lane is green:

- add Python 3.10 and 3.11 project classifiers alongside the existing 3.9
  classifier; and
- update Windows source/developer installation instructions to show the Python
  3.11 constraint and a matching `navigate-py311` conda environment.

Do not advertise Python 3.12 as a production-supported version while its lane
is experimental. The existing `requires-python = ">=3.9.7"` declaration does
not change.

## Verification and acceptance

Before pushing:

1. Confirm both new snapshots resolve the full Windows `.[dev]` graph and
   contain unique, sorted, exact pins.
2. Confirm the vendor-facing packages are present in both resolutions.
3. Validate the workflow with actionlint and repository pre-commit hooks.
4. Render the edited installation pages and inspect the generated commands.
5. Independently review the staged diff.

After pushing:

- Python 3.9, 3.10, and 3.11 required jobs must complete successfully;
- the Python 3.12 job must install its constrained environment and its test
  result must be recorded, even though failure is non-blocking;
- the scheduled unconstrained job must be skipped on the pull-request event;
- the PR must contain every current `develop` commit and remain mergeable; and
- the local branch and remote PR head must match.

If the actual Python 3.12 Windows installation cannot resolve the vendor stack,
remove that lane rather than masking an installation failure with
`continue-on-error`, and report the incompatible package as the blocker.
