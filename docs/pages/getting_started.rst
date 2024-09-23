Getting started
===============

LBAF currently supports Python 3.8 - 3.11. You can download Python `here <https://www.python.org/downloads/>`_ .

Create a virtual environment
----------------------------

To create and activate a virtual environment:

.. code-block:: shell

   python -m venv venv
   source venv/bin/activate

.. note::

   You can create separate virtual environments for different development branches. For example, a Python 3.8 environment for branch 125 could be named ``venv38-branch-125``. Within this environment, you can install ``lbaf`` as an editable package (see below).

Installation
------------

LBAF can be installed in two ways:

1. Install the LBAF Package *(recommended)*
   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   Users can easily install the latest release of LBAF with:

   .. code-block:: shell

      pip install lbaf

   Developers should clone the repo and install the package in editable mode:

   .. code-block:: shell

      git clone git@github.com:DARMA-tasking/LB-analysis-framework.git
      pip install -e LB-analysis-framework

2. Install Dependencies
   ^^^^^^^^^^^^^^^^^^^^

   If you do not wish to install LBAF as a package, simply clone the repo and install dependencies:

   .. code-block:: shell

      git clone git@github.com:DARMA-tasking/LB-analysis-framework.git
      pip install -r LB-analysis-framework/requirements.txt
