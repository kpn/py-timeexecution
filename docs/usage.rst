========
Usage
========

To use this package you decorate the functions you want to time its execution.
Every wrapped function will create a metric consisting of 3 default values:

- `name` - The name of the series the metric will be stored in
- `value` - The time it took in ms for the wrapped function to complete
- `hostname` - The hostname of the machine the code is running on

See the following example

.. code-block:: python

    from time_execution import settings, time_execution
    from time_execution.backends.influxdb import InfluxBackend
    from time_execution.backends.elasticsearch import ElasticsearchBackend

    # Setup the desired backend
    influx = InfluxBackend(host='influx', database='metrics', use_udp=False)
    elasticsearch = ElasticsearchBackend('elasticsearch', index='metrics')

    # Configure the time_execution decorator
    settings.configure(backends=[influx, elasticsearch])

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

And the following in Elasticsearch

.. code-block:: json

    [
        {
            "_index": "metrics-2016.01.28",
            "_type": "metric",
            "_id": "AVKIp9DpnPWamvqEzFB3",
            "_score": null,
            "_source": {
                "timestamp": "2016-01-28T14:34:05.416968",
                "hostname": "dfaa4928109f",
                "name": "__main__.hello",
                "value": 312
            },
            "sort": [
                1453991645416
            ]
        }
    ]

.. _usage-hooks:

Hooks
-----

`time_execution` supports hooks where you can change the metric before its
being sent to the backend.

With a hook you can add additional and change existing fields. This can be
useful for cases where you would like to add a column to the metric based on
the response of the wrapped function.

A hook will always get 3 arguments:

- `response` - The returned value of the wrapped function
- `exception` - The raised exception of the wrapped function
- `metric` - A dict containing the data to be send to the backend
- `func_args` - Original args received by the wrapped function.
- `func_kwargs` - Original kwargs received by the wrapped function.

From within a hook you can change the `name` if you want the metrics to be split
into multiple series.

See the following example how to setup hooks.

.. code-block:: python

    # Now lets create a hook
    def my_hook(response, exception, metric, func_args, func_kwargs):
        status_code = getattr(response, 'status_code', None)
        if status_code:
            return dict(
                name='{}.{}'.format(metric['name'], status_code),
                extra_field='foo bar'
            )

    # Configure the time_execution decorator, but now with hooks
    settings.configure(backends=[backend], hooks=[my_hook])

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

.. _grafana: http://grafana.org/


Custom Backend
--------------

Writing a custom backend is very simple, all you need to do is create a class
with a `write` method. It is not required to extend `BaseMetricsBackend`
but in order to easily upgrade I recommend u do.

.. code-block:: python

    from time_execution.backends.base import BaseMetricsBackend


    class MetricsPrinter(BaseMetricsBackend):
        def write(self, name, **data):
            print(name, data)
