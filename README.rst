Time Execution
==============

.. image:: https://secure.travis-ci.org/kpn-digital/py-timeexecution.svg?branch=master
    :target:  http://travis-ci.org/kpn-digital/py-timeexecution?branch=master

.. image:: https://img.shields.io/codecov/c/github/kpn-digital/py-timeexecution/master.svg
    :target: http://codecov.io/github/kpn-digital/py-timeexecution?branch=master

.. image:: https://img.shields.io/pypi/v/py-timeexecution.svg
    :target: https://pypi.python.org/pypi/py-timeexecution

.. image:: https://readthedocs.org/projects/py-timeexecution/badge/?version=latest
    :target: http://py-timeexecution.readthedocs.org/en/latest/?badge=latest


Features
--------

- Sending data to multiple backends
- Custom backends
- Hooks

Backends
--------

- InfluxDB 0.8


Installation
------------

.. code-block:: bash

    $ pip install py-timeexecution

Usage
-----

To use this package you decorate the functions you want to time its execution.
Every wrapped function will create a metric consisting of 3 default values:

- `name` - The name of the series the metric will be stored in
- `value` - The time it took in ms for the wrapped function to complete
- `hostname` - The hostname of the machine the code is running on

See the following example

.. code-block:: python

    from time_execution import configure, time_execution
    from time_execution.backends.influxdb import InfluxBackend

    # Setup the desired backend
    influx = InfluxBackend(host='localhost', database='metrics', use_udp=False)

    # Configure the time_execution decorator
    configure(backends=[influx])

    # Wrap the methods where u want the metrics
    @time_execution
    def hello():
        return 'World'

    # Now when we call hello() and we will get metrics in our backends
    hello()

This will result in an entry in the influxdb

.. code-block:: json

    [
        {
            "name": "__main__.hello",
            "columns": [
                "time",
                "sequence_number",
                "value",
                "hostname",
            ],
            "points": [
                [
                    1449739813939,
                    1111950001,
                    312,
                    "machine.name",
                ]
            ]
        }
    ]


Hooks
-----

`time_execution` supports hooks where you can change the metric before its
being send to the backend.

With a hook you can add additional and change existing fields. This can be
useful for cases where you would like to add a column to the metric based on
the response of the wrapped function.

A hook will always get 3 arguments:

- `response` - The returned value of the wrapped function
- `exception` - The raised exception of the wrapped function
- `metric` - A dict containing the data to be send to the backend

From within a hook you can change the `name` if you want the metrics to be split
into multiple series.

See the following example how to setup hooks.

.. code-block:: python

    # Now lets create a hook
    def my_hook(response, exception, metric):
        status_code = getattr(response, 'status_code', None)
        if status_code:
            return dict(
                name='{}.{}'.format(metric['name'], status_code),
                extra_field='foo bar'
            )

    # Configure the time_execution decorator, but now with hooks
    configure(backends=[influx], hooks=[my_hook])

Manually sending metrics
------------------------

You can also send any metric you have manually to the backend. These will not
add the default values and will not hit the hooks.

See the following example.

.. code-block:: python

    loadavg = os.getloadavg()
    write_metric('cpu.load.1m', value=loadavg[0])
    write_metric('cpu.load.5m', value=loadavg[1])
    write_metric('cpu.load.15m', value=loadavg[2])
