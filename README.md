[![Unit Tests](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/code-quality.yml/badge.svg)](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/code-quality.yml)
[![Pylint](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/pylint.svg)](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/pylint.svg)
[![Coverage](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/coverage.svg)](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/coverage.svg)

## This is the repository for Load-Balancing Analysis Framework (LBAF)
### It contains the following subdirectories:
* `src`: Load-Balancing Simulator code
* `doc`: research and papers and related documents
* `data`: various data inputs or outputs
* `tests`: unit tests and acceptance tests

### Please check Wiki for more details:
[Load Balancing Analysis Framework Wikipedia](https://github.com/DARMA-tasking/LB-analysis-framework/wiki)

## Before starting

The LBAF is available from source only now.

Currently, the versions of Python are [Python 3.8](https://www.python.org/downloads/) and [Python 3.9](https://www.python.org/downloads/).

The recommended version is Python 3.8. This is because configuration key `save_meshes` is not supported with Python 3.9


Please mind your platform as well as proper 32 or 64 bit version.

Make sure you have all required Python packages installed with:
```shell
pip install -r requirements.txt
```

Requirements are divided into `LBAF dependencies` and `LBAF testing`.

`LBAF dependencies` are needed in order to LBAF to work.

`LBAF testing` are needed for testing purposes.

### Installing PyZoltan on MacOS/Linux

Open MPI is needed to be installed. For Ubuntu based distributions packages `openmpi-bin libopenmpi-dev` have to be installed.

One needs to clone PyZoltan repository:
```shell
cd <some-directory>
git clone https://github.com/pypr/pyzoltan.git
```

One needs to build and link PyZoltan. Easiest way is to use the script provided in PyZoltan repository:
```shell
cd <some-directory>/pyzoltan
# INSTALL_PREFIX is an ABSOLUTE path to the directory, where Zoltan will be installed
./build_zoltan.sh INSTALL_PREFIX
# One needs to export ZOLTAN as an environment variable
export ZOLTAN=$INSTALL_PREFIX
```

`ZOLTAN` environment variable is very important, and it's used when installing `PyZoltan`

One needs to install `PyZoltan` requirements with:
```shell
pip install -r <some-directory>/pyzoltan/requirements.txt
```

Last step is to install `PyZoltan` itself:
```shell
pip install pyzoltan --no-build-isolation
```

One could check if `PyZoltan` is correctly installed by trying to import zoltan:
```Python3
from pyzoltan.core import zoltan
```

## Configuration file

LBAF run base of configuration file which could be find here:
```shell
<project-path>/config/conf.yaml
```

Description of each parameter in configuration file could be found at the top of configuration file.

## Testing

In order to run tests locally one needs to install test dependencies:
```shell
cd <project-path>
tox
```

`tox` command will:
- run all test defined in `tox.ini`
- create `artifacts` directory in main project path
- in `artifacts` directory html coverage report and pylint report could be found

## Usage

### LBAF

In order to run LBAF:

```shell
lbaf -c <config-file-name>
```

or

```shell
cd <project-path>
python src/lbaf/Applications/LBAF_app.py -c <config-file-name>
```

`<config-file-name>` can be an absolute path or a relative path and can be defined using the `-c` argument. If not set the application will consider that your configration file is named `conf.yaml`
If `<config-file-name>` is a relative path then the application will search from the current working directory, then from the `<project-path>/config` directory.

### JSON data files Validator

JSON data files Validator validates VT data files against defined schema. It is located in the VT repository and can be found [here](https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/JSON_data_files_validator.py).


## Download into LBAF

A command can be used to only download the data files validator without running it
```shell
lbaf-vt-data-files-validator-loader
```
or
```shell
cd <project-path>
python src/lbaf/Utils/lbsJSONDataFilesValidatorLoader.py
```

The script is then saved to `<project-path>/src/lbaf/imported/JSON_data_files_validator.py`

## Download and Run from LBAF

it can be run with
```shell
lbaf-vt-data-files-validator
```
or
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

### VT data Extractor

VT data Extractor extracts phases from VT stats files.
VT data Extractor can be run using the following command:
```shell
lbaf-vt-data-extractor
```
or
```shell
cd <project-path>
python src/lbaf/Utils/lbsVTDataExtractor.py
```

#### Input arguments (defined at the bottom of a file)

* `input_data_dir`: str - path to dir with files to extract e.g. `"../data/<dir-with-files>"`
* `output_data_dir`: str - path to dir where files should be saved e.g. `"../output"` (will be created when doesn't exist)
* `phases_to_extract`: list - list of phases `[int or str]` e.g. `[0, 1, "2-4"]` will extract phases `[0, 1, 2, 3, 4]`
* `file_prefix`: str - data file prefix e.g. if filename is `stats.0.json`, then prefix should be set to "stats"
* `file_suffix`: str - data file suffix e.g. if filename is `stats.0.json`, then suffix should be set to "json"
* `compressed`: bool - when True, brotli must be imported and then output data will be compressed
* `schema_type`: str - should be `"LBDatafile"` or `"LBStatsfile"` depends on input data. Only `"LBStatsfile"` is supported
* `check_schema`: bool - when True, validates schema (more time-consuming)


[//]: # (## Getting Started with Docker)

Replace `<in_dir>` with path to existing directory which will be mapped with `/lbaf/in` in container

Replace `<out_dir>` with path to existing directory which will be mapped with `/lbaf/out` in container

Put `conf.yaml` inside mapped `<in_dir>` and set `output_dir` in `conf.yaml` to `/lbaf/out`

When using sample data from repository set `data_stem` in `conf.yaml` to e.g. `/lbaf/data/synthetic_lb_data/data`

When using other data put the data inside mapped `<in_dir>` and set `data_stem` in `conf.yaml` to e.g. `/lbaf/in/<your_data_dir>/<data_name_prefix>`

#### Building locally (otherwise docker image will be pulled from dockerhub):
```shell
cd <main_repository_directory>
docker build -t nganalytics/lbaf:latest . -f lbaf.Dockerfile
```

#### Running:
```shell
docker run -it -v "<out_dir>:/lbaf/out" -v "<in_dir>:/lbaf/in" nganalytics/lbaf "python /lbaf/src/lbaf/Applications/LBAF_app.py --config=/lbaf/in/conf.yaml" "/bin/bash"
# in order to exit container
exit
```

### Example use explained:

- container starts with interactive mode (stdout visible)

- two volumes are mounted(data exchange between host and container possible):

  - directory `<in_dir>` on the host and `/lbaf/in` is mount inside container

  - directory `<out_dir>` on the host and `/lbaf/out` is mount inside container

- docker image `nganalytics/lbaf`

- commands executed inside container:

  - sample LBAF usage:

    ```"python /lbaf/src/lbaf/Applications/LBAF_app.py --config=/lbaf/in/conf.yaml"```

  - command to stay inside container, after above command is completed:

[//]: # (    ```"/bin/bash"```)
