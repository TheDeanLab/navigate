# Python 3.11 and 3.12 Windows CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Python 3.11 as a constrained, required Windows CI environment and
Python 3.12 as a constrained, non-blocking experimental Windows environment,
while preserving Python 3.9/3.10 coverage and the single unconstrained scheduled
dependency canary.

**Architecture:** Store complete Windows `.[dev]` resolutions in one constraint
file per Python minor version. Route Python 3.9, 3.10, and 3.11 through the
existing required matrix; route Python 3.12 through a separate experimental job
with job-level `continue-on-error`. Keep the scheduled Python 3.10 latest-
dependencies job as the only unconstrained lane, and use real Windows job logs
to reconcile the provisional 3.11/3.12 snapshots before finalizing the PR.

**Tech Stack:** Python packaging metadata, `uv pip compile`, pip constraints,
GitHub Actions, pytest, Codecov, reStructuredText, Sphinx, pre-commit, actionlint,
Git/GitHub CLI.

## Global Constraints

- Work only in the isolated worktree
  `/Users/Dean/Documents/GitHub/navigate/.worktrees/pr1179-resolve-conflicts` on
  `kdean/pr1179-resolve-conflicts`; push to PR #1179's `origin/update-deps2` only
  after local verification.
- Fetch `origin/develop` before implementation and immediately before the final
  push. The left side of `git rev-list --left-right --count
  origin/develop...HEAD` must be `0`.
- Do not change `requires-python = ">=3.9.7"`, remove Python 3.9/3.10, add a
  Python 3.12 classifier, or constrain the scheduled latest-dependencies job.
- Do not change application behavior. These are dependency, CI, metadata, and
  documentation changes, so semantic configuration validation replaces a new
  source-level unit test.
- Preserve unrelated user changes. Use `apply_patch` for repository edits and
  inspect the worktree before every commit.

---

### Task 1: Generate deterministic Windows 3.11 and 3.12 constraints

**Files:**

- Create: `constraints/windows-py311.txt`
- Create: `constraints/windows-py312.txt`

**Interface:** Each file is the complete, exact-version input consumed by both
`pip install -c ... -e ".[dev]"` and setup-python's pip cache key. The editable
`navigate-micro` project and pip itself are excluded.

- [ ] **Step 1: Confirm the branch still contains current develop**

  Run:

  ```bash
  git fetch --prune origin develop update-deps2
  git status --short --branch
  git rev-list --left-right --count origin/develop...HEAD
  ```

  Expected: clean worktree apart from this uncommitted plan, correct isolated
  branch, and `0` commits missing from `origin/develop`. If develop advanced,
  merge `origin/develop` before generating snapshots and recheck.

- [ ] **Step 2: Produce fresh Windows-targeted resolutions outside the repo**

  Run:

  ```bash
  constraint_tmp=$(mktemp -d)
  uv pip compile pyproject.toml --extra dev --python-platform windows --python-version 3.11 --no-annotate --no-header --output-file "$constraint_tmp/windows-py311.raw"
  uv pip compile pyproject.toml --extra dev --python-platform windows --python-version 3.12 --no-annotate --no-header --output-file "$constraint_tmp/windows-py312.raw"
  rg -n '^(pipython|nidaqmx|nitypes|hightime|pyserial|pyusb|numpy|scipy|opencv-python-headless|tifffile)==' "$constraint_tmp"/*.raw
  ```

  Expected: both compiles succeed, and both raw resolutions contain every
  vendor-facing and compiled/scientific package named in the final command.

- [ ] **Step 3: Add normalized snapshots with provisional provenance**

  For each raw file, retain only exact `distribution==version` lines, use the
  normalized distribution spelling emitted by uv, sort package names with
  `LC_ALL=C sort -f`, and create the repository file with `apply_patch`.

  Use this header form, substituting only the Python minor version:

  ```text
  # Fully resolved Windows CPython 3.11 development environment.
  # Provisional source: uv Windows-target resolution from pyproject.toml [dev].
  # Replace this provenance with the first successful Windows job URL, then
  # run the complete constrained test suite before finalizing this snapshot.
  # The editable navigate-micro package and pip are intentionally excluded.
  ```

  Do not add setuptools provisionally. Add it later only if the actual
  setup-python Windows environment reports it in `pip freeze --all`.

- [ ] **Step 4: Validate syntax, ordering, uniqueness, and satisfiability**

  Run:

  ```bash
  for file in constraints/windows-py311.txt constraints/windows-py312.txt; do
    test -z "$(rg -n -v '^(#.*|$|[a-z0-9][a-z0-9._-]*==[^=[:space:]]+)$' "$file")"
    diff -u <(rg -v '^(#|$)' "$file") <(rg -v '^(#|$)' "$file" | LC_ALL=C sort -f)
    test "$(rg -v '^(#|$)' "$file" | cut -d= -f1 | tr '[:upper:]' '[:lower:]' | wc -l | tr -d ' ')" = "$(rg -v '^(#|$)' "$file" | cut -d= -f1 | tr '[:upper:]' '[:lower:]' | sort -u | wc -l | tr -d ' ')"
    for package in pipython nidaqmx nitypes hightime pyserial pyusb; do
      rg -i "^${package}==" "$file"
    done
  done

  constraint_check_tmp=$(mktemp -d)
  uv pip compile pyproject.toml --extra dev --python-platform windows --python-version 3.11 -c constraints/windows-py311.txt --no-annotate --no-header --output-file "$constraint_check_tmp/windows-py311.checked"
  uv pip compile pyproject.toml --extra dev --python-platform windows --python-version 3.12 -c constraints/windows-py312.txt --no-annotate --no-header --output-file "$constraint_check_tmp/windows-py312.checked"
  git diff --check
  ```

  Expected: no malformed or duplicate entries, sorting diffs are empty, all
  vendor packages are found, and both constrained compiles succeed.

- [ ] **Step 5: Commit the constraint snapshots**

  Run:

  ```bash
  git add constraints/windows-py311.txt constraints/windows-py312.txt docs/superpowers/plans/2026-07-31-python311-python312-windows-ci.md
  git diff --cached --check
  git diff --cached --stat
  git commit -m "Add Python 3.11 and 3.12 Windows constraints"
  ```

---

### Task 2: Add required 3.11 and experimental 3.12 workflow lanes

**Files:**

- Modify: `.github/workflows/push_checks.yaml`

**Interface:** The `test` matrix remains the branch-protection-facing required
job family. The separate `experimental-python` job advertises Python 3.12's
non-blocking status explicitly. Both constrained paths print the installed
environment so snapshots can be audited against real Windows installations.

- [ ] **Step 1: Extend the required matrix with Python 3.11**

  Add this entry after Python 3.10:

  ```yaml
          - operating-system: windows-latest
            python-version: "3.11"
            python-tag: py311
  ```

  Do not change the generic constraint, cache, coverage, diagnostics, or Codecov
  expressions: the existing `${{ matrix.python-tag }}` wiring must select
  `constraints/windows-py311.txt`, `.coverage.py311`, and the `py311` Codecov
  flag automatically.

- [ ] **Step 2: Make required installed-package provenance visible**

  Immediately after `Install dependencies` in the required matrix, add:

  ```yaml
      - name: Record resolved environment
        run: python -m pip freeze --all
  ```

  This is intentionally diagnostic output, not a generated file committed by
  CI.

- [ ] **Step 3: Add the separate experimental Python 3.12 job**

  Insert this job before `latest-dependencies`:

  ```yaml
  experimental-python:
    name: Experimental Python 3.12
    if: github.event_name != 'schedule'
    continue-on-error: true
    runs-on: windows-latest
    timeout-minutes: 45
    env:
      MPLBACKEND: Agg
      NAVIGATE_RUN_PLUGIN_INTEGRATION: "1"
      COVERAGE_FILE: .coverage.py312
    steps:
      - uses: actions/checkout@v7
      - name: Set up Python 3.12
        uses: actions/setup-python@v7
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: constraints/windows-py312.txt
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -c constraints/windows-py312.txt -e ".[dev]"
      - name: Record resolved environment
        run: python -m pip freeze --all
      - name: Test with pytest
        timeout-minutes: 35
        run: python -m pytest
      - name: Dump Python processes (Windows)
        if: ${{ failure() }}
        shell: pwsh
        run: |
          Write-Host "Tasklist snapshot for python processes:"
          tasklist /v /fo table | Select-String -Pattern "python"
          Write-Host "Detailed process snapshot for python executables:"
          Get-CimInstance Win32_Process |
            Where-Object { $_.Name -match '^python(3)?(\.exe)?$' } |
            Select-Object ProcessId, ParentProcessId, Name, CommandLine |
            Format-List
  ```

  Keep this job outside the required matrix and omit Codecov. Do not alter the
  scheduled Python 3.10 job; it remains the only unconstrained install.

- [ ] **Step 4: Lint and inspect event semantics**

  If `actionlint` is not installed, download the latest official macOS arm64
  release to a temporary directory without modifying the repository:

  ```bash
  actionlint_tmp=$(mktemp -d)
  gh release download --repo rhysd/actionlint --pattern 'actionlint_*_darwin_arm64.tar.gz' --dir "$actionlint_tmp"
  tar -xzf "$actionlint_tmp"/actionlint_*_darwin_arm64.tar.gz -C "$actionlint_tmp"
  "$actionlint_tmp/actionlint" .github/workflows/push_checks.yaml
  ```

  Then inspect the relevant structure:

  ```bash
  rg -n 'python-version|python-tag|experimental-python|continue-on-error|github.event_name|pip install|Codecov|latest-dependencies' .github/workflows/push_checks.yaml
  git diff --check
  ```

  Expected: actionlint exits zero; required and experimental jobs skip schedule;
  the advisory job runs only on schedule; exactly one install command omits
  `-c constraints/`.

- [ ] **Step 5: Commit the workflow**

  Run:

  ```bash
  git add .github/workflows/push_checks.yaml
  git diff --cached --check
  git diff --cached
  git commit -m "Test Python 3.11 and experimental 3.12"
  ```

---

### Task 3: Advertise supported 3.11 environments without promoting 3.12

**Files:**

- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `docs/source/01_getting_started/03_software_installation.rst`
- Modify: `docs/source/03_contributing/02_developer_install/02_developer_install.rst`

**Interface:** Package metadata declares 3.9, 3.10, and 3.11 support. User and
developer Windows commands select the constraint matching the interpreter.
Python 3.12 remains visible only in CI as experimental. This task starts only
after the first required Python 3.11 Windows run is green.

- [ ] **Step 1: Push the CI infrastructure and gate support claims on 3.11**

  Run:

  ```bash
  git fetch --prune origin develop update-deps2
  git rev-list --left-right --count origin/develop...HEAD
  git status --short --branch
  git push origin HEAD:update-deps2
  gh pr checks 1179 --repo TheDeanLab/navigate --watch --interval 30
  initial_run_id=$(gh run list --repo TheDeanLab/navigate --branch update-deps2 --workflow push_checks.yaml --event pull_request --limit 1 --json databaseId --jq '.[0].databaseId')
  gh run view "$initial_run_id" --repo TheDeanLab/navigate --json jobs --jq '.jobs[] | {name, status, conclusion, url}'
  ```

  Expected: the left count is `0`, the tree is clean, and the required Python
  3.11 Windows job concludes successfully. Stop before changing classifiers or
  user documentation if the 3.11 job is not green. Record the 3.12 install and
  test outcome, but its test conclusion does not gate this task.

- [ ] **Step 2: Update supported Python classifiers**

  In `pyproject.toml`, keep the existing Python 3.9 classifier and add:

  ```toml
      "Programming Language :: Python :: 3.10",
      "Programming Language :: Python :: 3.11",
  ```

  Do not change `requires-python` and do not add a Python 3.12 classifier.

- [ ] **Step 3: Add the Python 3.11 source-install command to README**

  Immediately after the Windows Python 3.10 example, add:

  ```console
  # Windows with Python 3.11
  pip install -c constraints/windows-py311.txt -e ".[dev]"
  ```

- [ ] **Step 4: Add Python 3.11 to production and development source docs**

  In `03_software_installation.rst`, add matching examples:

  ```console
  # Windows with Python 3.11
  pip install -c constraints/windows-py311.txt .
  ```

  and:

  ```console
  # Windows with Python 3.11
  pip install -c constraints/windows-py311.txt -e ".[dev]"
  ```

  Revise the warning against mixing versions so it says the constraint must
  match the environment's Python minor version, rather than naming only 3.9
  and 3.10.

- [ ] **Step 5: Add the Python 3.11 developer environments**

  In `02_developer_install.rst`, add the constrained venv install command and
  this conda block after Python 3.10:

  ```console
  # Or Python 3.11
  conda create -n navigate-py311 python=3.11
  conda activate navigate-py311
  (navigate-py311) C:\Users\Username\Code> cd navigate
  (navigate-py311) C:\Users\Username\Code\navigate> pip install -c constraints/windows-py311.txt -e ".[dev]"
  ```

  Keep Python 3.9 and 3.10 examples unchanged. Do not add Python 3.12 user
  instructions.

- [ ] **Step 6: Render and inspect the documentation**

  Run:

  ```bash
  conda run -n navigate make -C docs html -j 15
  rg -n 'windows-py311|navigate-py311|Python 3.11' docs/build/html/01_getting_started/03_software_installation.html docs/build/html/03_contributing/02_developer_install/02_developer_install.html
  rg -n 'Programming Language :: Python :: 3\.(9|10|11|12)|requires-python' pyproject.toml
  git diff --check
  ```

  Expected: Sphinx completes, rendered HTML contains the Python 3.11 commands,
  classifiers are present only for 3.9-3.11, and `requires-python` is unchanged.
  Record any pre-existing Sphinx warnings separately; do not hide new warnings.

- [ ] **Step 7: Commit metadata and documentation**

  Run:

  ```bash
  git add pyproject.toml README.md docs/source/01_getting_started/03_software_installation.rst docs/source/03_contributing/02_developer_install/02_developer_install.rst
  git diff --cached --check
  git diff --cached
  git commit -m "Document supported Python 3.11 environments"
  ```

---

### Task 4: Perform local policy checks and independent review

**Files:**

- Verify all files changed in Tasks 1-3

**Interface:** This gate proves the repository artifacts are internally
consistent before using Windows CI as the authoritative installation test.

- [ ] **Step 1: Re-run all deterministic local checks from a clean tree**

  Run:

  ```bash
  git status --short --branch
  pre-commit run --all-files
  git diff --check
  uv pip compile pyproject.toml --extra dev --python-platform windows --python-version 3.11 -c constraints/windows-py311.txt --no-annotate --no-header --output-file /tmp/navigate-windows-py311.checked
  uv pip compile pyproject.toml --extra dev --python-platform windows --python-version 3.12 -c constraints/windows-py312.txt --no-annotate --no-header --output-file /tmp/navigate-windows-py312.checked
  conda run -n navigate make -C docs html -j 15
  ```

  Run the temporary actionlint binary from Task 2 again. Expected: checks exit
  zero except already documented, pre-existing Sphinx warnings; no hook may
  leave an unreviewed modification.

- [ ] **Step 2: Review the complete branch diff**

  Run:

  ```bash
  git diff --stat e42dee11f...HEAD
  git diff e42dee11f...HEAD -- .github/workflows/push_checks.yaml pyproject.toml README.md constraints docs/source docs/superpowers
  git log --oneline e42dee11f..HEAD
  ```

  Invoke `superpowers:requesting-code-review` for an independent review against
  the approved design. Address every correctness finding, rerun affected checks,
  and commit any review fixes with a focused message.

- [ ] **Step 3: Confirm the worktree is ready to publish**

  Run:

  ```bash
  git status --short --branch
  git diff --check
  ```

  Expected: clean worktree and only the intended commits ahead of
  `origin/update-deps2`.

---

### Task 5: Push the documented environment and reconcile Windows snapshots

**Files:**

- Modify if required: `constraints/windows-py311.txt`
- Modify if required: `constraints/windows-py312.txt`

**Interface:** GitHub Actions' Windows environments are authoritative for wheel
availability and runner-provided packages. Their logs replace provisional
constraint provenance and determine whether 3.12 remains eligible.

- [ ] **Step 1: Refresh develop and push to PR #1179**

  Run:

  ```bash
  git fetch --prune origin develop update-deps2
  git rev-list --left-right --count origin/develop...HEAD
  git status --short --branch
  git push origin HEAD:update-deps2
  ```

  Expected before push: the left count is `0` and the worktree is clean. If
  develop advanced, merge it, rerun Task 4, then push.

- [ ] **Step 2: Monitor the pull-request workflow and capture job identities**

  Run:

  ```bash
  gh pr checks 1179 --watch --interval 30
  run_id=$(gh run list --repo TheDeanLab/navigate --branch update-deps2 --workflow push_checks.yaml --event pull_request --limit 1 --json databaseId --jq '.[0].databaseId')
  gh run view "$run_id" --repo TheDeanLab/navigate --json url,status,conclusion,jobs
  ci_log=$(mktemp)
  gh run view "$run_id" --repo TheDeanLab/navigate --log > "$ci_log"
  rg -n 'Experimental Python 3.12|Python 3.11|Successfully installed|^-e |navigate-micro|pip==|setuptools==|passed|failed|ERROR' "$ci_log"
  ```

  Expected: required 3.9, 3.10, and 3.11 jobs pass; 3.12 completes its install
  step and reports its test result; scheduled latest-dependencies is skipped.
  A 3.12 test failure is reportable but non-blocking. A 3.12 installation or
  vendor-wheel failure is not acceptable.

- [ ] **Step 3: Reconcile each new snapshot with `pip freeze --all` output**

  Compare the 3.11 and 3.12 `Record resolved environment` sections with the
  corresponding constraint. Exclude only pip and the editable
  `navigate-micro` line. Add the runner's setuptools exact version if present;
  do not add packages visible only inside pip's isolated build environment.

  Obtain the exact Actions job URLs:

  ```bash
  gh run view "$run_id" --repo TheDeanLab/navigate --json jobs --jq '.jobs[] | select(.name | contains("3.11") or contains("3.12")) | {name, url}'
  ```

  Replace each provisional source line with the literal URL reported for its
  matching 3.11 or 3.12 job.

  Apply any pin/header corrections with `apply_patch`, then rerun Task 1's
  syntax/order/uniqueness/constrained-resolution checks.

  If Python 3.12 cannot install the full vendor stack on Windows, remove the
  experimental job and its production-facing constraint rather than allowing
  `continue-on-error` to mask the install failure. Record the incompatible
  package in the handoff.

- [ ] **Step 4: Commit provenance and push the reconciled snapshots**

  If reconciliation changed files, run:

  ```bash
  git add constraints/windows-py311.txt constraints/windows-py312.txt
  git diff --cached --check
  git diff --cached
  git commit -m "Record green Windows constraint provenance"
  git push origin HEAD:update-deps2
  ```

  Monitor the new run with the commands in Step 2. The final constrained run,
  not the provisional run, must satisfy the acceptance conditions.

---

### Task 6: Final PR verification and handoff

**Files:**

- No new files expected

**Interface:** The final branch must be current, mergeable, reproducible, and
identical to the remote PR head.

- [ ] **Step 1: Verify final checks and PR state**

  Run:

  ```bash
  gh pr checks 1179 --repo TheDeanLab/navigate
  gh pr view 1179 --repo TheDeanLab/navigate --json url,headRefName,headRefOid,baseRefName,mergeable,mergeStateStatus
  git fetch --prune origin develop update-deps2
  git rev-list --left-right --count origin/develop...HEAD
  git rev-parse HEAD
  git rev-parse origin/update-deps2
  git status --short --branch
  ```

  Expected: required 3.9/3.10/3.11 checks pass; the 3.12 install succeeded and
  its test outcome is recorded; the scheduled canary is skipped; the PR is
  mergeable; no current develop commit is missing; local and remote SHAs match;
  the worktree is clean.

- [ ] **Step 2: Report the result precisely**

  Provide the pushed commit SHA, PR URL, required lane conclusions, Python 3.12
  install and test conclusions, constraint provenance job URLs, local validation
  commands, develop containment result, and mergeability state. Distinguish a
  protection-policy `BLOCKED` state from an actual merge conflict.
