# Changelog


## 6.1.0 (2022-01-03)

### New

* NEW: Added new optional parameter "pipeline" to use document pre-processing in Elasticsearch. [Ricardo Alves]

### Optimizations

* OPT: Changed readme to markdown and fixed Python versions in setup.py. [Ricardo Alves]



## 6.0.0 (2022-01-03)

### Optimizations

* OPT: Using github actions instead of travis-ci. [Ricardo Alves]

### Other

* BREAK: Drop support for Python3.6. Add Python 3.9 and 3.10. [Ricardo Alves]



## 5.1.0 (2021-01-04)

### New

* NEW: flag to skip index creation on class instantiation. [Bart Veraart]

### Optimizations

* OPT: Speed up error_resilience test by decreasing max_retries. [Bart Veraart]

* OPT: update readme with some comments about starting elasticsearch. [Bart Veraart]



## 5.0.0 (2020-12-01)

### Other

* BREAK: drop old python versions, refactor CI. [Denis Kovalev]


## 4.1.2 (2019-11-05)

### Fixes

* FIX: update the version of fqn decorators to enable time async parameterization. [Denis Kovalev]


## 4.1.1 (2019-08-02)

### Fixes

* FIX: improve logging. [kammala]

### Optimizations

* OPT: use black and optimize build process. [kammala]

  - move test unrelated environment out of tox
  - use black and change isort settings accordingly
  - unpin flake8

* OPT Added changelog using gitchangelog and makefile target. [Ricardo Alves]

* OPT Improved readme with addtional badges and info regarding example usage with ElasticsSearch. [Ricardo Alves]



## 4.1.0 (2019-05-10)

### New

* NEW: Pass func/method in hooks. [Stanislav Evseev]



## 4.0.0 (2019-05-03)

### New

* NEW: Added specifying set of hooks for time_execution decorator. [Stanislav Evseev]

### Fixes

* FIX Fixed travis file. [Ricardo Alves]

* FIX Fixed travis configuration. [Ricardo Alves]

### Other

* Added new kafka backend. [Stanislav Evseev]


## 3.3.0 (2018-05-16)

### Other

* ElasticSearch 6.x support. [Pavel Perestoronin]


## 3.2.0 (2018-02-20)

### Fixes

* FIX Make threaded backend multiprocess-safe. [Pavel Perestoronin]


## 3.1.0 (2017-07-11)

### New

* NEW Add async decorator. [Ivan Mirić]

  For Python >=3.5 only.

### Changes

* CHANGED number of replicas in ElasticSearch template. [Sergey Panfilov]

* CHANGED create ElasticSearch index following the index name pattern. [Sergey Panfilov]

### Fixes

* FIX end the thread if the parent thread died. [Bart Veraart]

### Optimizations

* OPT Set thread name. [Bart Veraart]

### Other

* ElasticSearch 5 support. [Sergey Panfilov]

* FIXED lint error in threaded module. [Sergey Panfilov]

* Fix elasticsearch version to 2. [Sergey Panfilov]


## 1.10.4 (2016-10-04)

### Fixes

* FIX workaround TypeError in queue module. [Sergey Panfilov]


## 1.10.3 (2016-09-29)

### Fixes

* FIX TypeError if the queue in ThreadedBackend is gone. [Sergey Panfilov]


## 1.10.2 (2016-09-09)

### Fixes

* FIX index origin metric attribute. [Sergey Panfilov]


## 1.10.1 (2016-09-07)

### Fixes

* FIX make sure the worker stops. [Sergey Panfilov]


## 1.10.0 (2016-09-07)

### Fixes

* FIX duplicate pip call in makefile. [Sergey Panfilov]

* FIX threaded backend and tests. [Sergey Panfilov]

* FIX elasticsearch backend error resilience test. [Sergey Panfilov]

### Optimizations

* OPT add bulk write to elasticsearch backend. [Sergey Panfilov]

* OPT Implement async threaded backend. [Sergey Panfilov]


## 1.9.0 (2016-07-19)

### Fixes

* FIX name collision of mapping template. [Sergey Panfilov]

### Optimizations

* OPT improve usage documentation and describe package settings. [Sergey Panfilov]

* OPT add optional origin setting. [Sergey Panfilov]

### Other

* Update setup version to 1.9.0. [Sergey Panfilov]


## 1.8.0 (2016-07-14)

### New

* NEW make time_execution resilient to ElasticSearch backend errors. [Sergey Panfilov]

### Other

* Bump setup version to 1.8.0. [Sergey Panfilov]


## 1.7.1 (2016-06-29)

### Other

* Fix setup.py version. [Sergey Panfilov]


## 1.7.0 (2016-06-29)

### Fixes

* FIX naming collisions of package, module and decorator. [Sergey Panfilov]


## 1.6.1 (2016-05-13)

### Fixes

* FIX use six to properly retrieve exceptions based on sys.exc_info. [Mattias Sluis]


## 1.6.0 (2016-05-12)

### Optimizations

* OPT simplify time_execution decorator by basing it on the base Decorator class. [Mattias Sluis]


## 1.5.0 (2016-05-10)

### New

* NEW added setup.py to alloe pip -e installs. [Niels Lensink]

### Fixes

* FIX Sphinx doc requirements. [Mattias Sluis]

### Optimizations

* OPT reuse fqn that has been determined on init. [Mattias Sluis]

* OPT keep the github repo with the py prefix. [Niels Lensink]

* OPT use new name of the pkgversion dependency. [Niels Lensink]

### Other

* Update readme with proper badges. [Niels Lensink]


## 1.4.0 (2016-03-12)

### Optimizations

* OPT use new name of the pkgversion dependency. [Niels Lensink]

* OPT implemented pkgsettings and renamed py-timeexecution to timeexecution. [Niels Lensink]

* OPT added proper classifiers to the setup.py. [Niels Lensink]


## 1.3.0 (2016-02-01)

### New

* NEW elasticsearch backend. [Niels Lensink]

* NEW Update README.rst with new func_args and func_kwargs. [nimiq]

### Optimizations

* OPT test return values of the hooks inside the hooks unittests. [Niels Lensink]


## 1.2.0 (2016-01-26)

### New

* NEW Add wrapped function's original args and kwargs. [nimiq]


## 1.1.0 (2016-01-21)

### New

* NEW settings option duration_field. This configures the name of the field where we store the duration. [Niels Lensink]

### Optimizations

* OPT updated docs. [Niels Lensink]


## 1.0.3 (2015-12-14)

### Fixes

* FIX trying to workaround travis not picking up tags, travis#1675. [Enrique Paz]


## 1.0.2 (2015-12-14)

### Fixes

* FIX removed unused COVERAGE Makefile var. [Enrique Paz]

### Optimizations

* OPT updated docs and made some functions protected. [Niels Lensink]

* OPT updated readme. [Niels Lensink]

* OPT make sure the coverage reports get cleaned each run. [Niels Lensink]

* OPT removed unused env in tox. [Niels Lensink]


## 1.0.1 (2015-12-08)

### Optimizations

* OPT updated coverage. [Niels Lensink]

* OPT added xml report for code coverage. [Niels Lensink]


## 1.0.0 (2015-12-07)

### Other

* Initial commit. [Niels Lensink]


