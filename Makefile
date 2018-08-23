.PHONY: all
all: init lint

.PHONY: init
init: virtualenv

.PHONY: virtualenv
virtualenv: venv/bin/activate
	venv/bin/pip install -U pip
	venv/bin/pip install flake8 isort

venv/bin/activate:
	which virtualenv || pip install virtualenv
	virtualenv venv
	echo '*' > venv/.gitignore

.PHONY: lint
lint:
	venv/bin/flake8 *.py
	venv/bin/isort -y *.py
