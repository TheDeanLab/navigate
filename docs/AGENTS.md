# Documentation Agent Guide

This guide gives future agents context for writing and updating documentation in this repository.

## Goal

Write accessible documentation for a broad user base, including people with little or no programming experience.

## Core Expectations

- Use plain language first and define jargon/acronyms at first mention.
- Prefer step-by-step, task-oriented instructions.
- Assume some readers are not comfortable with command-line workflows.
- Use direct, practical tone.
- Use the project name as `**navigate**`.

## Source and Tooling

- Documentation sources live in `docs/source/`.
- Write docs in reStructuredText (`.rst`) only.
- Build with Sphinx (`docs/source/conf.py`).
- `autosectionlabel` is enabled with document prefixing; explicit labels are still preferred for stable references.

## Build and Validation

From `docs/`, preferred local build command is:

```bash
conda run -n navigate make html -j 15
```

Optional:

```bash
conda run -n navigate make linkcheck
```

Treat warnings as actionable, especially missing references, missing images, and malformed RST.

## Authoring Rules

- Prefer Sphinx roles over plain backticks where applicable.
- Use explicit labels for major sections/pages and cross-reference with `:ref:`.
- Reference sections/pages directly; avoid “see above/below”.
- Avoid generic link text like “here”; use descriptive link labels.
- Update `.. toctree::` entries whenever page structure changes.
- Include meaningful image `:alt:` text.
- Fix typos and grammar while editing.

## Hardware Docs Conventions

For files under `docs/source/02_user_guide/01_supported_hardware/`:

- Every page should define a top-level reference label near the top of the file.
- Avoid orphan pages: if a page is referenced for installation details (for example
  camera driver setup), it must be included in a visible `.. toctree::` in that section.
- Keep directives lowercase and consistent (`.. note::`, `.. warning::`, `.. tip::`).
- In `hardware_home.rst`, keep a short preflight callout that:
  - states Windows-first hardware support (with Linux used in some environments),
  - points users to software installation/configuration prerequisites,
  - points users to Virtual Devices mode (`navigate -sh`) when hardware is not yet connected.
- Keep the hardware devices toctree concise (`:maxdepth: 2`).
- In `camera.rst`, keep the local driver-installation toctree for:
  - `dcam_api.rst`
  - `pvcam.rst`

## Preferred Sphinx Roles

- `:ref:` internal sections
- `:doc:` pages
- `:guilabel:` UI labels/buttons
- `:menuselection:` menu paths
- `:kbd:` keyboard shortcuts
- `:command:` terminal commands
- `:file:` file paths
- `:code:` inline code snippets

## Current Getting Started Structure

Keep this sequence in the home page toctree:

1. `01_getting_started/01_minimum_computer_requirements`
2. `01_getting_started/02_power_management`
3. `01_getting_started/03_software_installation`
4. `01_getting_started/04_launching_navigate`
5. `01_getting_started/05_configuring_navigate`

Do not reintroduce the removed `01_quick_start` page.

## Session-Specific Content Decisions

- Landing page:
  - Keep a clear **Start Here** callout to Software Installation.
  - Keep **Need Help?** with link to GitHub issues: <https://github.com/TheDeanLab/navigate/issues>
  - Keep citation link to PubMed: <https://pubmed.ncbi.nlm.nih.gov/39261640/>
  - Keep the full citation text for the 2024 *Nature Methods* paper on the home page.
  - OS compatibility message: primarily Windows; also used on Linux in some environments.
- Minimum requirements:
  - Explicitly note that **navigate** can be developed/tested on a laptop.
  - For operating microscopes, recommend workstation/server-class systems due to PCIe expansion needs.
  - Include the short “Required Power/Firmware Settings” checklist here.
  - Keep full deep-dive power guidance in `02_power_management.rst`, linked via the `power_management` reference label.
- Software installation:
  - Stratify by strategy: Conda + PyPI, `venv` + PyPI, GitHub install, and `uv`.
  - In `venv` instructions, include changing directory (`cd`) to target workspace before creating `.venv`.
  - In GitHub install, note Windows users may need Git for Windows: <https://git-scm.com/install/windows>
  - Include synthetic launch command (`navigate -sh`) where useful for validation.
- Launching:
  - Keep first-launch flow: `navigate -sh` -> configure via `navigate -c` -> launch normally with `navigate`.
  - Include command-line argument overview early, at least:
    - `-h` / `--help`
    - `-sh` / `--synthetic-hardware`
    - `-c` / `--configurator`
- Configuring:
  - `05_configuring_navigate.rst` is a short quick-start bridge (5-7 concise steps), not deep internals.
  - Explain what `configuration.yaml` is and where it is saved.
  - State that the config file is delicate; add devices one-by-one and validate incrementally.
  - Mention manual editing can unlock advanced functionality.
  - Link to advanced details in `02_user_guide/04_microscope_setup/01_software_configuration/software_configuration.rst`.

## Screenshot Update Workflow

Use `docs/capture_gui.py` for documentation screenshots.

- Run through Python (not as a bare executable path):

```bash
conda run -n navigate python docs/capture_gui.py --list
```

- Key selectors:
  - `--all`
  - `--group <group>`
  - `--capture <id>`
  - `--manifest <json>`
  - `--configurator-only` (compatibility shortcut)
- The capture path expects `mss` in docs dependencies; do not add a PIL fallback.
- For UI pages that are not fully rendered, increase settle timing:
  - `--passes <n>`
  - `--delay-ms <ms>`
- All generated GUI screenshots should be written under:
  - `docs/source/images/`

## Avoid Duplication

- Keep Getting Started pages action-oriented and concise.
- Keep advanced details in User Guide/Software Configuration pages.
- Prefer linking to canonical sections rather than copying large blocks of technical detail.
