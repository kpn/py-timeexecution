========
Settings
========

Package configuration is done through using package settings:

.. code-block:: python

    from time_execution import settings
    settings.configure()


Parameters accepted by `configure` method are described bellow.

backends
--------

Optional parameter, equals to empty list by default, accepts a list of :doc:`api/time_execution.backends` instances.

hooks
-----

Optional parameter, equals to empty list by default, accepts the list of callable, see :ref:`usage-hooks`.

duration_field
--------------

Optional parameter, equals to `"value"` by default.

origin
------

Optional parameter, equals to `None` by default. If specified, then sent metrics will have `"origin"` attribute, which can be used to identify origin of the metric, when `time_execution` package is used in multiple applications.
