Testing
=======

Testing in LBAF are divided into two types of tests:
  * Unit Tests
  * Acceptance Tests

Requirements for testing
------------------------

A file which contains all required packages for testing purposes can be found under:

* `<project-path>/requirements.txt`, where `<x>` stands for python version.

Unit testing
------------

* `Unit Tests` are checking for low level logic - functions, methods, classes

In order to run tests locally one needs to install test dependencies (`Before starting <before_starting.html>`_):

.. code-block:: bash

  cd <project-path>
  tox

`tox` command will:

* run all test defined in `tox.ini`
* create `artifacts` directory in main project path `<project-path>/artifacts`
* in `<project-path>/artifacts` directory html coverage report and pylint report could be found:

  * coverage report (html and text)
  * pylint report (text)

* all tests as well as coverage and pylint output are printed to stdout as well

Badges creation
---------------

In order to create a badges for further use in repository:

.. code-block:: bash

  cd <project-path>
  mkdir badges
  PYLINT_SCORE=$(sed -n 's/^Your code has been rated at \([-0-9.]*\)\/.*/\1/p' ./artifacts/pylint.txt)
  anybadge --label=pylint --file=badges/pylint.svg --value=$PYLINT_SCORE 2=red 4=orange 8=yellow 10=green
  COVERAGE_SCORE=$(sed -n '/TOTAL/,/%/p' artifacts/coverage.txt | rev | cut -d" " -f1 | rev | tr -d % )
  anybadge --value=$COVERAGE_SCORE --file=badges/coverage.svg coverage

Acceptance tests
----------------

`Acceptance Tests` are checking for correctness of business logic - based on input data test is checking for expected output

Synthetic Blocks Test Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

  # Specify input
  from_data:
    data_stem: "../synthetic-blocks/synthetic-dataset-blocks"
    phase_ids:
      - 0
  # Specify work model
  work_model:
    name: AffineCombination
    parameters:
      beta: 0.
      gamma: 0.

  # Specify balancing algorithm
  algorithm:
    name: InformAndTransfer
    parameters:
      n_iterations: 8
      n_rounds: 4
      fanout: 4
      order_strategy: element_id
      criterion: Tempered
      max_objects_per_transfer: 8
      deterministic_transfer: True

  # Specify output
  #logging_level: debug
  #overwrite_validator: False
  #check_schema: False
  logging_level: info
  output_dir: /__w/LB-analysis-framework/LB-analysis-framework/output
  output_file_stem: output_file
  generate_meshes:
    x_ranks: 2
    y_ranks: 2
    z_ranks: 1
    object_jitter: 0.5

Stepper Test Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

  # Specify input
  from_data:
    data_stem: "../data/nolb-8color-16nodes-11firstphases/data"
    phase_ids:
      - 0
      - 1
      - 2
      - 3
      - 4
      - 5
      - 6
      - 7
      - 8
      - 9
      - 10

  # Specify work model
  work_model:
    name: AffineCombination
    parameters:
      beta: 1.0e-8
      gamma: 0.

  # Specify algorithm
  algorithm:
    name: PhaseStepper

  # Specify output
  #logging_level: debug
  #overwrite_validator: False
  #check_schema: False
  log_to_file: /__w/LB-analysis-framework/LB-analysis-framework/log.txt
  generate_multimedia: False
  output_dir: /__w/LB-analysis-framework/LB-analysis-framework/output
  output_file_stem: output_file
  generate_meshes:
    x_ranks: 8
    y_ranks: 4
    z_ranks: 1
    object_jitter: 0.5
