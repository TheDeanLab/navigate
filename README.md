<h1 align="center">
<img src="https://github.com/TheDeanLab/navigate/blob/develop/src/navigate/view/icon/mic.ico?raw=true" />

navigate
<h2 align="center">
	open source light sheet microscope control
</h2>
</h1>


[![Tests](https://github.com/TheDeanLab/navigate/actions/workflows/push_checks.yaml/badge.svg)](https://github.com/TheDeanLab/navigate/actions/workflows/push_checks.yaml)
[![codecov](https://codecov.io/gh/TheDeanLab/navigate/branch/develop/graph/badge.svg?token=270RFSZGG5)](https://codecov.io/gh/TheDeanLab/navigate)

**navigate** is an open source Python package for control of light-sheet microscopes.
It allows for easily reconfigurable hardware setups and automated acquisition rotuines.

### Quick install

Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html#latest-miniconda-installer-links).

```
conda create -n navigate python=3.9.7
conda activate navigate
pip install git+https://github.com/TheDeanLab/navigate.git
```

To test, run `conda activate navigate` and launch in synthetic hardware mode with `navigate
-sh`. Developers will have to install additional dependencies with
`pip install -e '.[dev]'`.
### Documentation
Please refer to and contribute to the documentation, which can be found on GitHub Pages: [https://thedeanlab.github.io/navigate/](https://thedeanlab.github.io/navigate/).

### Command Line Arguments

Below are the optional arguments that can be passed to the navigate software:

- `-h, --help`
  Provides information on the optional arguments that can be passed to **navigate**.
- `-sh, --synthetic_hardware`
  Open the software without any hardware attached for testing
  and setting up a new system.
- `-c, --configurator`
  Open the **navigate** configuration wizard, which provides a
  graphical interface for setting up the hardware configuration.
- `-d`
  Enables the debugging menu in the software.
- `--config-file`
  Pass a non-default `configuration.yaml` file to **navigate**.
- `--experiment_file`
  Pass a non-default `experiment.yaml` file to **navigate**.
- `--gui-config-file`
  Pass a non-default `gui_config.yaml` file to **navigate**.
- `--waveform-constants-file`
  Pass a non-default waveform constants file to **navigate**.
- `--rest_api_file`
  Pass a non-default REST API file to **navigate**.
- `--logging_config`
  Pass a non-default logging configuration file to **navigate**.
