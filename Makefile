.PHONY: clean all build install kernel-install test

SITE-PACKAGES = $(shell pip show notebook | grep Location | cut -d ' ' -f 2)
CODEMIRROR = $(SITE-PACKAGES)/notebook/static/components/codemirror
CODEMIRROR-AGDA = $(CODEMIRROR)/mode/agda
$(info CODEMIRROR-AGDA: $(CODEMIRROR-AGDA))

all: build local-install codemirror-install # kernel-install

test: build local-install kernel-install codemirror-install
	jupyter nbconvert --to notebook --execute example/example.ipynb  --output example-output.ipynb

build: dist/agda_kernel-0.3-py3-none-any.whl

dist/agda_kernel-0.3-py3-none-any.whl: setup.py src/agda_kernel/install.py src/agda_kernel/kernel.py
	python setup.py bdist_wheel

local-install: build
	pip install .
	# python -m pip install --force-reinstall dist/agda_kernel-0.3-py3-none-any.whl

# run after the agda_kernel module is installed
kernel-install: local-install
	python -m agda_kernel.install

codemirror-install: codemirror-agda/agda.js
	mkdir -p $(CODEMIRROR-AGDA)
	cp codemirror-agda/agda.js $(CODEMIRROR-AGDA)

pip-upload: build
	python -m twine upload dist/*

pip-install:
	pip install agda_kernel

committ:
	git add 

clean:
	rm -rf agda_kernel.egg-info build dust
