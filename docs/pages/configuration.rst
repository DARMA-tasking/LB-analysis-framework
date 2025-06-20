Configuration file
==================

Below a structure of YAML file explained as well as example `*.yml` configuration.

Parameters
----------

* **PARAMETER NAME IN CONFIGURATION [TYPE]**: description
* **work_model**: work model to be used

  * **name [str]**: in `LoadOnly`, `AffineCombination`
  * **parameters [dict]**: optional parameters specific to each work model

* **algorithm**: balancing algorithm to be used

  * **name [str]**: in `InformAndTransfer`, `BruteForce`
  * **parameters [dict]**: parameters specitic to each algorithm

    * **`InformAndtransfer`**:

      * **criterion [str]**: in `Tempered` (default), `StrictLocalizer`
      * **n_iterations [int]**: number of load-balancing iterations
      * **deterministic_transfer [bool]**: (default: False) for deterministic transfer
      * **n_rounds [int]**: number of information rounds
      * **fanout [int]**: information fanout index
      * **order_strategy [str]**: ordering of objects for transfer in `arbitrary` (default), `element_id`, `increasing_times`, `decreasing_times`, `fewest_migrations`, `small_objects`

    * **`BruteForce`**:

      * **skip_transfer [bool]**: (default: False) skip transfer phase

    * **`PhaseStepper`**:

* **logging_level [str]**: set to `info`, `debug`, `warning` or `error`
* **log_to_file [str]**: filepath to save the log file (optional)
* **x_procs [int]**: number of procs in x direction for rank visualization
* **y_procs [int]**: number of procs in y direction for rank visualization
* **z_procs [int]**: number of procs in z direction for rank visualization
* **data_stem [str]**: base file name of VT load logs
* **phase_ids [list or str]**: list of ids of phase to be read in VT load logs e.g. [1, 2, 3] or "1-3"
* **map_file [str]**: base file name for VT object/proc mapping
* **file_suffix [str]**: file suffix of VT data files (default: "json")
* **output_dir [str]**: output directory (default: '.')
* **overwrite_validator [bool]**: download and overwrite JSON_data_files_validator from VT (default: True)
* **check_schema [bool]**: checking schema in VT input files (optional, default: True)
* **generate_meshes [bool]**: generate mesh outputs (default: False)
* **generate_multimedia [bool]**: generate multimedia visualization (default: False)
* **n_objects [int]**: number of objects
* **n_mapped_ranks [int]**: number of initially mapped processors
* **communication_degree [int]**: object communication degree (no communication if 0)
* **load_sampler**: description of object loads sampler)

  * **name [str]**: in `uniform`, `lognormal`
  * **parameters [list]**: parameters e.g. 1.0,10.0 for lognormal

* **volume_sampler**: description of object communication volumes sampler

  * **name [str]**: in `uniform`, `lognormal`
  * **parameters [list]**: parameters e.g. 1.0,10.0 for lognormal


Example configuration
---------------------

.. code-block:: yaml

    # Specify input
    from_data:
      data_stem: "../data/synthetic_lb_data/data"
      phase_ids:
        - 0
    # Specify work model
    work_model:
      name: AffineCombination
      parameters:
        beta: 0.
        gamma: 0.
        delta: 0.

    # Specify balancing algorithm
    algorithm:
    #  name: BruteForce
      name: InformAndTransfer
      parameters:
        n_iterations: 8
        n_rounds: 4
        fanout: 4
        order_strategy: arbitrary
        criterion: Tempered
        max_objects_per_transfer: 8
        deterministic_transfer: True

    # Specify output
    #logging_level: debug
    #overwrite_validator: False
    check_schema: False
    generate_multimedia: False
    output_dir: ../../../output
    output_file_stem: output_file
    generate_meshes:
      x_ranks: 2
      y_ranks: 2
      z_ranks: 1
      object_jitter: 0.5

