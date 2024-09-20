[![Unit Tests](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/code-quality.yml/badge.svg)](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/code-quality.yml)
[![Pylint](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/pylint.svg)](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/pylint.svg)
[![Coverage](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/coverage.svg)](https://raw.githubusercontent.com/DARMA-tasking/LB-analysis-framework/deploy-badges/coverage.svg)

# This is the repository for the Load-Balancing Analysis Framework (LBAF)
### It contains the following subdirectories:
* `src`: Load-Balancing Simulator code
* `doc`: Research papers and related documents
* `data`: Various data inputs or outputs
* `tests`: Unit tests and acceptance tests

_Please refer to our [documentation](https://darma-tasking.github.io/lbaf_docs/index.html) for more details._

---

### Table of Contents

- [Getting Started](#getting-started)
- [Installation](#installation)
- [Testing](#testing)
- [Usage](#usage)
- [Additional Programs](#additional-programs)
- [LBAF In Literature](#lbaf-in-literature)

---

## Getting Started

LBAF currently supports Python 3.8 - 3.11. You can download Python [here](https://www.python.org/downloads/).

### Optional: Create a virtual environment *(recommended in development)*

To create and activate a virtual environment:
```shell
python -m venv venv
source venv/bin/activate
```

> [!NOTE]
> You can create separate virtual environments for different development branches. For example, a Python 3.8 environment for branch 125 could be named `venv38-branch-125`. Within this environment, you can install `lbaf` as an editable package (see below).

## Installation

LBAF can be installed in two ways:

<details>
<summary><b>1. Install the LBAF Package <i>(recommended)</i></b></summary>

<br />

Users can easily install the latest release of LBAF with:

```shell
pip install lbaf
```

Developers should clone the repo and install the package in editable mode:

```shell
git clone git@github.com:DARMA-tasking/LB-analysis-framework.git
pip install -e LB-analysis-framework
```

</details>
<details>
<summary><b>2. Install Dependencies</b></summary>

<br />

If you do not wish to install LBAF as a package, simply clone the repo and install dependencies:

```shell
git clone git@github.com:DARMA-tasking/LB-analysis-framework.git
pip install -r LB-analysis-framework/requirements.txt
```

</details>

## Testing

Begin by installing the test dependencies in `requirements.txt`.

```shell
pip install tox coverage pylint pytest anybadge
```

Then, to run all tests locally:

```shell
cd <project-path>
tox
```

The `tox` command will:
- run all tests defined in `tox.ini`
- create the `artifacts` directory in main project path
- create an html coverage report and a pylint report within the `artifacts` directory

## Usage

If the `lbaf` package is installed, LBAF can be run using the following command:

```shell
lbaf -c <config-file-path>
```

If dependencies were installed instead, LBAF must be run from source:

```shell
cd <project-path>
python src/lbaf/Applications/LBAF_app.py -c <config-file-path>
```

### Configuration File

The configuration file is a YAML file that specifies how LBAF will run.

`<config-file-path>` can be an absolute path or a relative path to your configuration file.

A description of each parameter in the configuration file can be found [here](https://darma-tasking.github.io/lbaf_docs/configuration.html), and sample configurations can be found in the `config` directory.

### Visualization

LBAF can optionally leverage [`vt-tv`](https://github.com/DARMA-tasking/vt-tv), a DARMA-tasking tool built off of [`VTK`](https://vtk.org/), to visualize the work-to-rank mappings, communications, and memory usage of a run.

To get started, you will need to build `VTK` (instructions [here](https://gitlab.kitware.com/vtk/vtk/-/blob/master/Documentation/docs/build_instructions/build.md)).

Then, clone the `vt-tv` repository and install the Python bindings:

```shell
git clone https://github.com/DARMA-tasking/vt-tv.git
VTK_DIR=/path/to/vtk/build pip install vt-tv
```

Once `vt-tv` has been installed, you may include visualization parameters in the configuration file. Sample parameters are found (commented out) at the bottom of `config/conf.yaml`.

For more instructions on building and using `vt-tv`, refer to the [documentation](https://github.com/DARMA-tasking/vt-tv?tab=readme-ov-file).

### Verbosity

To print a list of all Quantities of Interest (QOI) supported by LBAF, add a verbosity argument to the run command:

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

## Additional Programs

<details>
<summary><b> JSON data files validator</b></summary>

<br />

JSON data files Validator validates vt data files against defined schema. It is located in the vt repository and can be found [here](https://raw.githubusercontent.com/DARMA-tasking/vt/develop/scripts/JSON_data_files_validator.py).

#### Download into LBAF

If the `lbaf` package is installed, run:

```shell
lbaf-vt-data-files-validator-loader
```

Otherwise, run from source:

```shell
cd <project-path>
python src/lbaf/Utils/lbsJSONDataFilesValidatorLoader.py
```

The script will be saved to `<project-path>/src/lbaf/imported/JSON_data_files_validator.py`

#### Run from LBAF

If the `lbaf` package is installed, run:

```shell
lbaf-vt-data-files-validator
```

Otherwise, run from source:

```shell
cd <project-path>
python src/lbaf/imported/JSON_data_files_validator.py
```

_Note: This command automatically downloads the `JSON_data_files_validator.py` script if needed._

#### Usage

These commands assume that LBAF was installed as a package. When running from source, replace the run command as noted above.

For single file:

```shell
# With relative path
lbaf-vt-data-files-validator --file_path=../../../data/nolb-8color-16nodes-data/data.0.json

# With absolute path
lbaf-vt-data-files-validator --file_path=<project-path>/data/nolb-8color-16nodes-data/data.0.json
```

For many files in the same directory:

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
</details>

<details>
<summary><b>vt Data Extractor</b></summary>

<br />
The vt Data Extractor extracts phases from vt stats files.

#### Usage

To run using the lbaf package:

```shell
lbaf-vt-data-extractor
```
To run from source:

```shell
cd <project-path>
python src/lbaf/Utils/lbsVTDataExtractor.py
```

#### Input arguments

* `input_data_dir`: str - path to dir with files to extract e.g. `"./data/<dir-with-files>"`
* `output_data_dir`: str - path to dir where files should be saved e.g. `"./output"` (will be created when doesn't exist)
* `phases_to_extract`: list - list of phases `[int or str]` e.g. `[0, 1, "2-4"]` will extract phases `[0, 1, 2, 3, 4]`
* `file_prefix`: str - data file prefix e.g. if filename is `stats.0.json`, then prefix should be set to "stats"
* `file_suffix`: str - data file suffix e.g. if filename is `stats.0.json`, then suffix should be set to "json"
* `compressed`: bool - when True, brotli must be imported and then output data will be compressed
* `schema_type`: str - should be `"LBDatafile"` or `"LBStatsfile"` depends on input data. Only `"LBStatsfile"` is supported
* `check_schema`: bool - when True, validates schema (more time-consuming)

</details>

<details>
<summary><b>vt Data Maker</b></summary>

<br />

The vt Data Maker generates a dataset of JSON files that may be used throughout the DARMA-tasking organization. The generated files are compatible with `LBAF`, `vt-tv`, and `vt`.

If the `lbaf` package is installed, run with:

```sh
lbaf-vt-data-files-maker <args>
```

Otherwise, run:

```shell
python src/lbaf/Utils/lbsJSONDataFilesMaker.py <args>
```

The program can be run interactively with the `--interactive` argument.

Otherwise, it accepts a pre-written specification file (`--spec-file`) and the file stem for the resulting data files (`--data-stem`).

Further documentation, including usage and examples, can be found within the script itself.

</details>

## LBAF in Literature

### [Optimizing Distributed Load Balancing for Workloads with Time-Varying Imbalance](https://ieeexplore.ieee.org/document/9556089)

"This paper explores dynamic load balancing algorithms used by asynchronous many-task (AMT), or ‘task-based’, programming models to optimize task placement for scientific applications with dynamic workload imbalances."
