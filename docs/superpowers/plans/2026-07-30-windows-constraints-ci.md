# Windows Constraints and CI Implementation Plan

**Goal:** Make the Windows Python 3.9 and 3.10 environments reproducible while
retaining one scheduled unconstrained dependency canary.

**Architecture:** Store complete, Python-specific Windows resolution snapshots
as pip constraint files. Required CI and Windows source-install documentation
select the matching snapshot. A separate scheduled-only job deliberately
omits constraints.

**Tech Stack:** pip constraints, GitHub Actions, Sphinx/reStructuredText.

---

### Task 1: Add the green Windows resolution snapshots

**Files:**
- Create: `constraints/windows-py39.txt`
- Create: `constraints/windows-py310.txt`

1. Extract the resolved package set from each green Windows job in workflow run
   `30544828353`, including dependencies already present in the runner.
2. Exclude pip and the editable `navigate-micro` package.
3. Normalize each entry to `distribution==version`, sort case-insensitively,
   and add provenance/regeneration comments.
4. Validate exact pins, ordering, uniqueness, and the expected direct
   dependencies for both Python versions.

### Task 2: Constrain required CI and add the canary

**Files:**
- Modify: `.github/workflows/push_checks.yaml`

1. Add the weekly schedule and prevent required matrix jobs from running for
   scheduled events.
2. Upgrade checkout, setup-python, and Codecov to the current v7 actions.
3. Enable setup-python pip caching with the matching constraint as the cache
   dependency path.
4. Install each required matrix environment with its matching constraint.
5. Add one scheduled-only Windows Python 3.10 job that installs without a
   constraint and runs pytest.
6. Parse and lint the workflow.

### Task 3: Document reproducible Windows source environments

**Files:**
- Modify: `README.md`
- Modify: `docs/source/01_getting_started/03_software_installation.rst`
- Modify: `docs/source/03_contributing/02_developer_install/02_developer_install.rst`

1. Show the Python 3.9 and 3.10 Windows constraint choices.
2. Apply the matching constraint to source production and development install
   commands.
3. Explain briefly that constraints reproduce tested versions without
   declaring transitives as project dependencies.
4. Build the documentation with warnings treated as errors.

### Task 4: Verify and publish

1. Run constraint validation, workflow linting, documentation build, targeted
   tests, formatting/policy checks, and `git diff --check`.
2. Review the final diff and confirm only intended files changed.
3. Commit the implementation, push the PR branch, and monitor all new Windows
   checks to completion.
