.PHONY: clean all build install kernel-install test

PIP=pip3
PYTHON=python3
SITE-PACKAGES = $(shell $(PIP) show notebook | grep Location | cut -d ' ' -f 2)
CODEMIRROR = $(SITE-PACKAGES)/notebook/static/components/codemirror
CODEMIRROR-AGDA = $(CODEMIRROR)/mode/agda
$(info CODEMIRROR-AGDA: $(CODEMIRROR-AGDA))

# Docker image name and tag
IMAGE:=yossarianlives/agda-notebook
TAG?=latest
# Shell that make should use
SHELL:=bash
# Can export DOCKER=podman in parent environment
DOCKER:=docker

all: build install codemirror-install docker-build docker-push # kernel-install

docker-build: DARGS?=
docker-build:
	$(DOCKER) build $(DARGS) --rm --force-rm -t $(IMAGE):$(TAG) .

docker-push: docker-build
	$(DOCKER) push $(IMAGE):$(TAG)

docker-run: ARGS?=
docker-run: DARGS?=
docker-run: PORT?=8888
docker-run: ## Make a container from a tagged image image
	$(DOCKER) run -it --rm -p $(PORT):8888 $(DARGS) $(IMAGE):$(TAG) $(ARGS)

test: build install kernel-install codemirror-install
	#jupyter nbconvert --to notebook --execute example/Example.ipynb  --output Example-output.ipynb

pytest: install
	pytest

build: dist/agda_kernel-0.64-py3-none-any.whl

dist/agda_kernel-0.64-py3-none-any.whl: setup.py src/agda_kernel/install.py src/agda_kernel/kernel.py
#	pylint src/agda_kernel/kernel.py
	$(PYTHON) setup.py bdist_wheel

install: build
	$(PIP) install .

# run after the agda_kernel module is installed
kernel-install: install
	$(PYTHON) -m agda_kernel.install

codemirror-install: codemirror-agda/agda.js
	mkdir -p $(CODEMIRROR-AGDA)
	cp codemirror-agda/agda.js $(CODEMIRROR-AGDA)

pip-upload: build
	$(PYTHON) -m twine upload dist/*

pip-install:
	$(PIP) install agda_kernel

commit:
	git add 

clean:
	rm -rf agda_kernel.egg-info build dust
