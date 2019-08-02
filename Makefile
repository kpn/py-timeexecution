# This Makefile requires the following commands to be available:
# * virtualenv
# * python3.6
# * docker
# * docker-compose

DOCKER_COMPOSE:=$(shell which docker-compose)


.PHONY: pyclean
pyclean:
	find . -name "*.pyc" -delete
	rm -rf *.egg-info build
	rm -rf coverage.xml .coverage

.PHONY: docsclean
docsclean:
	rm -rf docs/_build/
	rm -rf docs/api/

.PHONY: clean
clean: pyclean docsclean
	@rm -rf venv
	@rm -rf .tox

venv:
	python3.6 -m venv venv
	venv/bin/pip install -U pip -q
	venv/bin/pip install -r requirements.txt

.PHONY: test
test: venv pyclean
	venv/bin/tox

test/%: venv pyclean
	venv/bin/tox -- $*

.PHONY: lint
lint: venv
	venv/bin/flake8 time_execution tests
	venv/bin/isort -rc -c time_execution tests
	venv/bin/black --check time_execution tests

.PHONY: format
format: venv
	venv/bin/isort -rc time_execution tests
	venv/bin/black --verbose time_execution tests

.PHONY: docs
docs: venv docsclean
	venv/bin/python docs/apidoc.py -T -M -d 2 -o docs/api time_execution
	venv/bin/sphinx-build -W -b html docs docs/_build/html

.PHONY: docker
docker:
	$(DOCKER_COMPOSE) run --rm --service-ports app bash

docker/%:
	$(DOCKER_COMPOSE) run --rm --service-ports app make $*

setup.py: venv
	venv/bin/python setup_gen.py
	venv/bin/python setup.py sdist
	venv/bin/twine check dist/*

.PHONY: publish
publish: setup.py
	-rm setup.py
	$(MAKE) setup.py
	venv/bin/twine upload dist/*

.PHONY: build
build: clean venv lint test setup.py

changelog:
	venv/bin/gitchangelog
