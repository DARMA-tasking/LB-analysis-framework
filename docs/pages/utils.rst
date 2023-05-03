Utils
=====

Utils available in LBAF repository

JSON data files Validator
-------------------------

JSON data files Validator validates VT data files against defined schema.

Schema is defined `HERE <https://github.com/DARMA-tasking/vt/blob/develop/scripts/JSON_data_files_validator.py>`__

After use of `LBAF.py`, `JSON_data_files_validator.py` appears in:

* <project-path>/src/lbaf/imported/JSON_data_files_validator.py.

**Usage for single file:**

.. code-block:: bash

  # With relative path
  python JSON_data_files_validator.py --file_path=../../../data/8color-4node/data.0.json

  # With absolute path
  python JSON_data_files_validator.py --file_path=<project-path>/data/8color-4node/data.0.json

**Usage for many files in the same directory:**

.. code-block:: bash

  # With relative path
  python JSON_data_files_validator.py --dir_path=../../../data/8color-4node

  # With absolute path
  python JSON_data_files_validator.py --dir_path=<project-path>/data/8color-4node

  # Optionally one could pass --file_prefix and/or --file_suffix
  # When one passes files with given prefix/suffix or both will be validated
  # When no prefix and suffix will be given validator will find most common prefix and suffix in the directory
  # and will use them for validation process
  python JSON_data_files_validator.py --dir_path=../../data/8color-4node --file_prefix=data --file_suffix=json

VT data Extractor
-----------------

VT data Extractor extracts phases from VT stats files.

Location
^^^^^^^^

**VT data Extractor is located in:**

.. code-block:: bash

  <project-path>/src/lbaf/Utils/vt_data_extractor.py

Input explanation
^^^^^^^^^^^^^^^^^

**Input arguments (defined at the bottom of a file):**

* **input_data_dir: [str]** - path to dir with files to extract e.g. "../data/<dir-with-files>"
* **output_data_dir: [str]** - path to dir where files should be saved e.g. "../output" (will be created when doesn't exist)
* **phases_to_extract: [list]** - list of phases [int or str] e.g. [0, 1, "2-4"] will extract phases [0, 1, 2, 3, 4]
* **file_prefix: [str]** - data file prefix e.g. if filename is stats.0.json, then prefix should be set to "stats"
* **file_suffix: [str]** - data file suffix e.g. if filename is stats.0.json, then suffix should be set to "json"
* **compressed: [bool]** - when True, brotli must be imported and then output data will be compressed
* **schema_type: [str]** - should be "LBDatafile" or "LBStatsfile" depends on input data. Only "LBStatsfile" is supported
* **check_schema: [bool]** - when True, validates schema (more time-consuming)
