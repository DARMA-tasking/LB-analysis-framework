[![Unit Tests](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/unit-tests.yml)
[![Acceptance Tests](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/acceptance-tests.yml/badge.svg)](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/acceptance-tests.yml)

## This is the repository for Load-Balancing Simulation research
### It contains the following subdirectories:
* `src`: Load-Balancing Simulator code
* `doc`: research and papers and related documents
* `data`: various data inputs or outputs

## Before starting

The LBAF is available from source only now. It requires [Python 3.8](https://www.python.org/downloads/) to run.

Currently, the only working version of Python is 3.8. This is due to the compatibility of used packages.

Please mind your platform as well as proper 32 or 64 bit version.

Make sure you have all required Pyhon packages installed with:
```shell
pip install -r requirements-3.8.txt
```

Requirements are divided into `LBAF dependencies` and `LBAF testing`. 

`LBAF dependencies` are needed in order to LBAF to work.

`LBAF testing` are needed for testing purposes.

## Configuration file

LBAF run base of configuration file which could be find here:
```shell
<project-path>/src/lbaf/Applications/conf.yaml
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

In order to run LBAF from main project directory:
```shell
cd <project-path>
python src/lbaf/Applications/LBAF.py
```

### JSON data files Validator

JSON data files Validator validates VT data files against defined schema.

Schema is defined in `<project-path>/src/lbaf/IO/schemaValidator.py`.

JSON data files Validator is located in `<project-path>/src/lbaf/Utils/JSON_data_files_validator.py`.

Usage for single file:
```shell
# With relative path
python JSON_data_files_validator.py --file_path=../../../data/8color-4node/data.0.json

# With absolute path
python JSON_data_files_validator.py --file_path=<project-path>/data/8color-4node/data.0.json
```

Usage for many files in the same directory:
```shell
# With relative path
python JSON_data_files_validator.py --dir_path=../../../data/8color-4node

# With absolute path
python JSON_data_files_validator.py --dir_path=<project-path>/data/8color-4node

# Optionally one could pass --file_prefix and/or --file_suffix
# When one passes files with given prefix/suffix or both will be validated
# When no prefix and suffix will be given validator will find most common prefix and suffix in the directory 
# and will use them for validation process
python JSON_data_files_validator.py --dir_path=../../data/8color-4node --file_prefix=data --file_suffix=json
```

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