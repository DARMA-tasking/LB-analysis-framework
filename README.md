[![Unit Tests](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/unit-tests.yml)
[![Acceptance Tests](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/acceptance-tests.yml/badge.svg)](https://github.com/DARMA-tasking/LB-analysis-framework/actions/workflows/acceptance-tests.yml)

This is the repository for Load-Balancing Simulation research
It contains the following subdirectories:
* `src`: Load-Balancing Simulator code
* `doc`: research and papers and related documents
* `data`: various data inputs or outputs

## Getting Started with Docker
### Example use:

Replace `<in_dir>` with path to existing directory which will be mapped with `/lbaf/in` in container

Replace `<out_dir>` with path to existing directory which will be mapped with `/lbaf/out` in container
```shell
docker run -it -v "<out_dir>:/lbaf/out" -v "<in_dir>:/lbaf/in" nganalytics/lbaf "python src/Applications/NodeGossiper.py -l /lbaf/data/vt_example_lb_stats/stats -x 4 -y 2 -z 1 -s 0 -f 4 -k 4 -i 4 -c 1 -e" "/bin/bash"
```
### Example use explained:
- container starts with interactive mode (stdout visible)
- two volumes are mounted(data exchange between host and container possible):
  - directory `<in_dir>` on the host and `/lbaf/in` is mount inside container
  - directory `<out_dir>` on the host and `/lbaf/out` is mount inside container
- docker image `nganalytics/lbaf`
- commands executed inside container:
  - sample LBAF usage:
    ```"python src/Applications/NodeGossiper.py -l /lbaf/data/vt_example_lb_stats/stats -x 4 -y 2 -z 1 -s 0 -f 4 -k 4 -i 4 -c 1 -e"```
  - command to stay inside container, after above command is completed:
    ```"/bin/bash"```