[![Unit Tests](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/code-quality.yml/badge.svg)](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/code-quality.yml)
[![Pylint](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/pylint.svg)](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/pylint.svg)
[![Coverage](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/coverage.svg)](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/coverage.svg)

# This is the repository for Load-Balancing Analysis Framework (LBAF)
### It contains the following subdirectories:
* `src`: Load-Balancing Simulator code
* `doc`: research and papers and related documents
* `data`: various data inputs or outputs
* `tests`: unit tests and acceptance tests

### Please check Wiki for more details:
[Load Balancing Analysis Framework Wikipedia](https://github.com/DARMA-tasking/LB-analysis-framework/wiki)

## Before starting

`LBAF` currently supports [Python 3.8](https://www.python.org/downloads/) and [Python 3.9](https://www.python.org/downloads/).

The recommended version is Python 3.8. This is because configuration key `save_meshes` is not supported with Python 3.9


Please mind your platform as well as proper 32 or 64 bit version.

### Set up virtual environment(s) *(recommended in development)*

It is recommended in development mode to create and use virtual environments.
To be able to use virtual environments, please install the virtualenv package using the command `pip install virtualenv`.

To create and activate a virtual environment for LBAF supported Python versions:
```shell
python3.8 -m venv venv38
python3.9 -m venv venv39
. venv38/bin/activate
```
Please note that virtual environment names should be prefixed by 'venv' as a convention.
Once an environment has been created and is active you can install the LBAF package using `pip install -e .` or just the requirements using `pip install -r requirements.txt`.

### Install **LBAF** package
*Recommended in development except if multiple versions must run in the same environment*

If you don't need to install several versions of LBAF, you can install LBAF as a package in editable mode from the project directory.

From the project directory, run:
 ```shell
pip install -e .
```

This will automatically install the required dependencies.

*Note: pip package manager does not support hosting different versions of the same package in a single python environment*.

*Note: Although not required, it's common to locally install the project in "editable" or "develop" mode while you're working on it. This allows your project to be both installed and editable in project form.*

### Install dependencies

If LBAF has not been installed as a package (for example because you have multiple versions of LBAF on your machine), you will run LBAF differently.

Install the dependencies by running the following command:
```shell
cd <project-path>
pip install -r requirements.txt
```

In general, it is often recommended during development to use python virtual environments and it is possible to have also environments dedicated to some development branches. For example a Python3.8 environment for the branch 125 could be named "venv38-branch-125" and then you could install lbaf as a package in editable mode inside this environment only.

#### Requirements

Requirements are divided into `LBAF dependencies` and `LBAF testing`.

`LBAF dependencies` are needed in order to LBAF to work.

`LBAF testing` are needed for testing purposes.

## Testing

In order to run tests locally, one needs to install test dependencies:
```shell
cd <project-path>
tox
```

The `tox` command will:
- run all test defined in `tox.ini`
- create the `artifacts` directory in main project path
- create an html coverage report and a pylint report within the `artifacts` directory

## Usage

### LBAF

If the lbaf package is installed you can run LBAF using the following command:
```shell
lbaf -c <config-file-name>
```

Or run LBAF from source:

```shell
cd <project-path>
python src/lbaf/Applications/LBAF_app.py -c <config-file-name>
```

### Configuration file

`<config-file-name>` can be an absolute path or a relative path to your configuration file. It is defined using the `-c` argument. If not set, the application will use `<project-path>/config/conf.yaml` as your configuration file.

If `<config-file-name>` is a relative path then the application will search first from the current working directory, then from the `<project-path>/config` directory.

A description of each parameter in configuration file can be found at the top of configuration file.

### Verbosity

To print a list of all Quantities of Interest (QOI) supported by LBAF, add a verbosity argument to the above commands:

```shell
cd <project-path>
lbaf -c <config-file-name> -v <verbosity-level>
```

or

```shell
cd <project-path>
python src/lbaf/Applications/LBAF_app.py -c <config-file-name> -v <verbosity-level>
```

To output only the Rank QOI, use `-v 1`. Otherwise, to print both Rank and Object QOI, use `-v 2`.

## JSON data files Validator

JSON data files Validator validates VT data files against defined schema. It is located in the VT repository and can be found [here](https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/JSON_data_files_validator.py).


### Download into LBAF

To run using the lbaf package:
```shell
lbaf-vt-data-files-validator-loader
```
To run from source:
```shell
cd <project-path>
python src/lbaf/Utils/lbsJSONDataFilesValidatorLoader.py
```

The script is then saved to `<project-path>/src/lbaf/imported/JSON_data_files_validator.py`

### Download and Run from LBAF

To run using the lbaf package:
```shell
lbaf-vt-data-files-validator
```
To run from source:
```shell
cd <project-path>
python src/lbaf/imported/JSON_data_files_validator.py
```
This command automatically downloads the JSON_data_files_validator.py script if needed.


Usage for single file:
```shell
# With relative path
lbaf-vt-data-files-validator --file_path=../../../data/nolb-8color-16nodes-data/data.0.json

# With absolute path
lbaf-vt-data-files-validator --file_path=<project-path>/data/nolb-8color-16nodes-data/data.0.json
```

Usage for many files in the same directory:
```shell
# With relative path
lbaf-vt-data-files-validator --dir_path=../../../data/nolb-8color-16nodes-data

# With absolute path
lbaf-vt-data-files-validator --dir_path=<project-path>/data/nolb-8color-16nodes-data

# Optionally one could pass --file_prefix and/or --file_suffix
# When one passes files with given prefix/suffix or both will be validated
# When no prefix and suffix will be given validator will find most common prefix and suffix in the directory
# and will use them for validation process
lbaf-vt-data-files-validator --dir_path=../../data/nolb-8color-16nodes-data --file_prefix=data --file_suffix=json
```

## VT data Extractor

VT data Extractor extracts phases from VT stats files.

To run using the lbaf package:
```shell
lbaf-vt-data-extractor
```
To run from source:
```shell
cd <project-path>
python src/lbaf/Utils/lbsVTDataExtractor.py
```

#### Input arguments (defined at the bottom of a file)

* `input_data_dir`: str - path to dir with files to extract e.g. `"./data/<dir-with-files>"`
* `output_data_dir`: str - path to dir where files should be saved e.g. `"./output"` (will be created when doesn't exist)
* `phases_to_extract`: list - list of phases `[int or str]` e.g. `[0, 1, "2-4"]` will extract phases `[0, 1, 2, 3, 4]`
* `file_prefix`: str - data file prefix e.g. if filename is `stats.0.json`, then prefix should be set to "stats"
* `file_suffix`: str - data file suffix e.g. if filename is `stats.0.json`, then suffix should be set to "json"
* `compressed`: bool - when True, brotli must be imported and then output data will be compressed
* `schema_type`: str - should be `"LBDatafile"` or `"LBStatsfile"` depends on input data. Only `"LBStatsfile"` is supported
* `check_schema`: bool - when True, validates schema (more time-consuming)

## LBAF in Literature

### [Optimizing Distributed Load Balancing for Workloads with Time-Varying Imbalance](https://ieeexplore.ieee.org/document/9556089)

"This paper explores dynamic load balancing algorithms used by asynchronous many-task (AMT), or ‘taskbased’, programming models to optimize task placement for scientific applications with dynamic workload imbalances."

[//]: # (## Getting Started with Docker)

[//]: # (### Example use:)

[//]: # ()
[//]: # (Replace `<in_dir>` with path to existing directory which will be mapped with `/lbaf/in` in container)

[//]: # ()
[//]: # (Replace `<out_dir>` with path to existing directory which will be mapped with `/lbaf/out` in container)

[//]: # (```shell)

[//]: # (docker run -it -v "<out_dir>:/lbaf/out" -v "<in_dir>:/lbaf/in" nganalytics/lbaf "python src/Applications/NodeGossiper.py -l /lbaf/data/vt_example_lb_stats/stats -x 4 -y 2 -z 1 -s 0 -f 4 -k 4 -i 4 -c 1 -e" "/bin/bash")

[//]: # (```)

[//]: # (### Example use explained:)

[//]: # (- container starts with interactive mode &#40;stdout visible&#41;)

[//]: # (- two volumes are mounted&#40;data exchange between host and container possible&#41;:)

[//]: # (  - directory `<in_dir>` on the host and `/lbaf/in` is mount inside container)

[//]: # (  - directory `<out_dir>` on the host and `/lbaf/out` is mount inside container)

[//]: # (- docker image `nganalytics/lbaf`)

[//]: # (- commands executed inside container:)

[//]: # (  - sample LBAF usage:)

[//]: # (    ```"python src/Applications/NodeGossiper.py -l /lbaf/data/vt_example_lb_stats/stats -x 4 -y 2 -z 1 -s 0 -f 4 -k 4 -i 4 -c 1 -e"```)

[//]: # (  - command to stay inside container, after above command is completed:)

[//]: # (    ```"/bin/bash"```)
