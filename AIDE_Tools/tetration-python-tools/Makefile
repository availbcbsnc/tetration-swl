SPHINXOPTS    ?= -W
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docs
BUILDDIR      = build
VIRTUALENV = build/.venv
LOCAL_ENV = .venv

.PHONY: build
.ONESHELL:
build: clean
	python3 -m venv $(VIRTUALENV)
	. $(VIRTUALENV)/bin/activate
	pip install -U twine
	pip install -U wheel
	python3 setup.py sdist bdist_wheel

.PHONY: build-container
build-container:
	docker build . -t containers.cisco.com/aide/tetration-python-tools

### Sphinx 
.PHONY: help
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: Makefile
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: clean
clean:
	rm -rf build
	rm -rf *.egg-info
	rm -rf .eggs

.PHONY: check
.ONESHELL:
check: build
	. $(VIRTUALENV)/bin/activate
	twine check dist/*

.PHONY: install
.ONESHELL:
install:
	. $(LOCAL_ENV)/bin/activate
	pip install .

.PHONY: upload
.ONESHELL:
upload: check
	. $(VIRTUALENV)/bin/activate
	twine upload --repository-url https://engci-maven.cisco.com/artifactory/api/pypi/cx-aide-pypi-local dist/*

.PHONY: init
init:
	pip install -r requirements.txt

.PHONY: tox
tox:
	tox

.PHONY: create-module-docs
create-module-docs:
	sphinx-apidoc -M -T --force -e -o docs/reference/tetpyannotations tetpyannotations **constants**

.PHONY: display-coverage-report
display-coverage-report:
	coverage report -m

.PHONY: container-static-analysis
container-static-analysis:
	docker run -it --rm -v `PWD`:/repo containers.cisco.com/aide/static-analysis-tools sh 

.PHONY: local-clean
local-clean:
	rm -rf build
	rm -rf $(LOCAL_ENV)

.PHONY: local-env
.ONESHELL:
local-env:
	python3 -m venv $(LOCAL_ENV)
	. $(LOCAL_ENV)/bin/activate
	pip install .
