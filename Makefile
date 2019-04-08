
.PHONY: clean all build install kernel-install

all: build install kernel-install upload

build: dist/agda_kernel-0.2-py3-none-any.whl

dist/agda_kernel-0.2-py3-none-any.whl: setup.py agda_kernel/install.py agda_kernel/kernel.py
	python setup.py bdist_wheel

local-install: build
	python -m pip install --force-reinstall dist/agda_kernel-0.2-py3-none-any.whl

pip-install:
	pip install agda_kernel

# run after the agda_kernel module is installed
kernel-install: build
	python -m agda_kernel.install

upload: build
	python -m twine upload dist/*

clean:
	rm -rf agda_kernel.egg-info build dust