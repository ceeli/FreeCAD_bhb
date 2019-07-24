Settings/Parameter
==================

The Solver Framework has a great demand for user supplied settings because it
interfaces with a lot of external software and every user envrionment is a
little bit different. A more sophisticated abbroach than just using FreeCADs
Parameter System directely was taken to tackle this problem.

All options are abstracted away behind functions of the
:mod:`femsolver.settings` module. See the following module documentation for
more information. All parameters used in the background are documented in
:ref:`parameter-definitions`.

The ``settings`` Module
-----------------------

.. automodule:: femsolver.settings
   :members:


.. _parameter-definitions:

Parameter Definitions
---------------------

All parameers are children of
**User parameter:BaseApp/Preferences/Mod/Fem/**.

General Settings
~~~~~~~~~~~~~~~~

.. glossary::

   General/UseTempDirectory
      Let FreeCAD manage (create, delete) the working directories for all
      solver. Use temporary directories. If set
      :term:`General/UseBesideDirectory` and :term:`General/UseCustomDirectory`
      are always unset.

   General/UseBesideDirectory
      Create a directory in the same folder in which the FCStd file of the
      document is located. Use Subfolder for each solver (e.g. for a file
      ./mydoc.FCStd and a solver with the label Elmer002 use ./mydoc/Elmer002).
      If set :term:`General/UseTempDirectory` and
      :term:`General/UseCustomDirectory` are always unset.

   General/UseCustomDirectory
      Use directory set below. Create own subdirectory for every solver. Name
      directory after the solver label prefixed with the document name.  If set
      :term:`General/UseTempDirectory` and :term:`General/UseBesideDirectory`
      are always unset.

   General/CustomDirectoryPath
      If :term:`General/UseCustomDirectory` is set this option specifies the
      directory path as a string. Can be empty (``str``) if a different option
      for directory management is used.


Elmer Settings
~~~~~~~~~~~~~~

.. glossary::

   Elmer/UseStandardElmerLocation
      If set the hardcoded default binary name will be used to execute
      ElmerSolver. The value of :term:`Elmer/elmerBinaryPath` is ignored in
      that case. If unset the value of :term:`Elmer/elmerBinaryPath` is used
      instead.

   Elmer/elmerBinaryPath
      User supplied path to the ElmerSolver binary. Used only if
      :term:`Elmer/UseStandardElmerLocation` is unset.

   Elmer/UseStandardGridLocation
      If set the hardcoded default binary name will be used to execute
      ElmerGrid. The value of :term:`Elmer/gridBinaryPath` is ignored in
      that case. If unset the value of :term:`Elmer/gridBinaryPath` is used
      instead.

   Elmer/gridBinaryPath
      User supplied path to the ElmerGrid binary. Used only if
      :term:`Elmer/UseStandardGridLocation` is unset.


Calculix Settings
~~~~~~~~~~~~~~~~~

.. glossary::

   Ccx/UseStandardCcxLocation
      If set the hardcoded default binary name will be used to execute
      Calculix. The value of :term:`Ccx/ccxBinaryPath` is ignored in
      that case. If unset the value of :term:`Ccx/ccxBinaryPath` is used
      instead.

   Ccx/ccxBinaryPath
      User supplied path to the Calculix binary. Used only if
      :term:`Ccx/UseStandardCcxLocation` is unset.


Z88 Settings
~~~~~~~~~~~~

.. glossary::

   Z88/UseStandardZ88Location
      If set the hardcoded default binary name will be used to execute
      Z88. The value of :term:`Z88/z88BinaryPath` is ignored in
      that case. If unset the value of :term:`Z88/z88BinaryPath` is used
      instead.

   Z88/z88BinaryPath
      User supplied path to the Z88 binary. Used only if
      :term:`Z88/UseStandardZ88Location` is unset.
