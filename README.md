<h1 align="center">
  <img src="https://github.com/TheDeanLab/navigate/blob/develop/src/navigate/view/icon/mic.ico?raw=true" alt="navigate icon" />
  <br />
  navigate
</h1>

<p align="center"><strong>open source light-sheet microscope control</strong></p>

[![Published in Nature Methods](https://img.shields.io/badge/Published%20in-Nature%20Methods-blue)](https://doi.org/10.1038/s41592-024-02413-4)
[![GitHub Stars](https://img.shields.io/github/stars/TheDeanLab/navigate?style=social)](https://github.com/TheDeanLab/navigate)
[![PyPI Version](https://img.shields.io/pypi/v/navigate-micro)](https://pypi.org/project/navigate-micro/)
[![Python Versions](https://img.shields.io/pypi/pyversions/navigate-micro)](https://pypi.org/project/navigate-micro/)
[![Docs](https://github.com/TheDeanLab/navigate/actions/workflows/build_docs.yaml/badge.svg)](https://github.com/TheDeanLab/navigate/actions/workflows/build_docs.yaml)
[![Tests](https://github.com/TheDeanLab/navigate/actions/workflows/push_checks.yaml/badge.svg)](https://github.com/TheDeanLab/navigate/actions/workflows/push_checks.yaml)
[![codecov](https://codecov.io/gh/TheDeanLab/navigate/branch/develop/graph/badge.svg?token=270RFSZGG5)](https://codecov.io/gh/TheDeanLab/navigate)

**navigate** is an open-source Python package for light-sheet microscope control. It supports reconfigurable hardware setups and automated acquisition routines.

> **OS compatibility:** **navigate** is primarily used on Windows for microscope operation because many hardware drivers are Windows-focused. Linux and macOS are useful for development and limited testing.

## Documentation

Project documentation is published at: <https://thedeanlab.github.io/navigate/>

Key entry points:
- Getting Started: <https://thedeanlab.github.io/navigate/01_getting_started/03_software_installation.html>
- Configure navigate: <https://thedeanlab.github.io/navigate/01_getting_started/05_configuring_navigate.html>
- Developer Install: <https://thedeanlab.github.io/navigate/03_contributing/02_developer_install/02_developer_install.html>
- Contributing Guidelines: <https://thedeanlab.github.io/navigate/03_contributing/01_contributing_guidelines/01_contributing_guidelines.html>

## Quick Install (Conda + PyPI)

Install Miniconda: <https://docs.conda.io/en/latest/miniconda.html>

```bash
conda create -n navigate python=3.9.7
conda activate navigate
pip install navigate-micro
```

## First Launch (Recommended)

```bash
# 1) Validate in synthetic hardware mode
navigate -sh

# 2) Open the configurator to create/edit configuration files
navigate -c

# 3) Launch normally
navigate
```

## Install From Source (Developers)

```bash
git clone https://github.com/TheDeanLab/navigate.git
cd navigate
```

Install in editable mode with development dependencies:

```bash
# Windows (cmd/powershell)
pip install -e .[dev]

# Linux/macOS
pip install -e ".[dev]"
```

## Command Line Arguments

Run `navigate --help` for the complete list.

- `-h`, `--help`: show help text.
- `-c`, `--configurator`: open the configuration wizard.
- `-sh`, `--synthetic-hardware`: launch without attached hardware.
- `-d`: enable the debugging tool menu.
- `--config-file PATH`: use a non-default `configuration.yaml`.
- `--gui-config-file PATH`: use a non-default `gui_configuration.yml`.
- `--experiment-file PATH`: use a non-default `experiment.yml`.
- `--waveform-constants-file PATH`: use a non-default `waveform_constants.yml`.
- `--waveform-templates-file PATH`: use a non-default `waveform_templates.yml`.
- `--rest-api-file PATH`: use a non-default `rest_api_config.yml`.
- `--logging-config PATH`: use a non-default `logging.yml`.
- `--multi-positions-file PATH`: use a non-default `multi_positions.yml`.

## Contributing

If you plan to contribute, follow the contributor docs linked above. Before opening a PR, run:

```bash
pre-commit run --all-files
pytest
conda run -n navigate make -C docs html -j 15
```

Need help or want to report a bug? Open an issue:
<https://github.com/TheDeanLab/navigate/issues>
