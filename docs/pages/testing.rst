Testing
=======

In order to run tests locally one needs to install test dependencies:

.. code-block:: bash

  cd <project-path>
  tox

`tox` command will:

  * run all test defined in `tox.ini`
  * create `artifacts` directory in main project path
  * in `artifacts` directory html coverage report and pylint report could be found
