<h1 align="center">
<img src="./src/aslm/view/icon/mic.ico?raw=true" />

ASLM - Autonomous Software for Light Microscopy
</h1>

[![Tests](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/push_checks.yaml/badge.svg)](https://github.com/AdvancedImagingUTSW/ASLM/actions/workflows/push_checks.yaml)
[![codecov](https://codecov.io/gh/TheDeanLab/ASLM/branch/develop/graph/badge.svg?token=270RFSZGG5)](https://codecov.io/gh/TheDeanLab/ASLM)

ASLM is an open source Python package for control of light-sheet microscopes. It allows for easily reconfigurable hardware setups and automated acquisition rotuines.

### Quick install

Download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html#latest-miniconda-installer-links).

```
conda create -n aslm python=3.9.7
pip install git+https://github.com/TheDeanLab/ASLM.git
```

To test, run `conda activate aslm` and launch in synthetic hardware mode with `aslm
-sh`. Developers will have to install additional dependencies with
`pip install -e '.[dev]'`.
### Documentation
Please refer to and contribute to the documentation, which can be found on GitHub Pages: [https://thedeanlab.github.io/ASLM/](https://thedeanlab.github.io/ASLM/).

### Command Line Arguments

* optional arguments:
	*  -h, --help            show this help message and exit

* Input Arguments:
  	* -sh, --synthetic_hardware
  	* --config_file CONFIG_FILE
  	* --experiment_file EXPERIMENT_FILE
  	* --etl_const_file ETL_CONST_FILE
	*  --rest_api_file REST_API_FILE
  	* --logging_config LOGGING_CONFIG

### Authors
* Kevin Dean
* Zach Marin
* Xiaoding 'Annie' Wang
* Dax Collison
* Sampath Rapuri
* Samir Mamtani
* Renil Gupta
* Andrew Jamieson
