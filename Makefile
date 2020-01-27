NAME=txrudp
PIP=pip
PYTHON=python2
SETUP=setup.py
TESTPATH=./tests

.PHONY: all build check clean dist distclean install uninstall wheel

all: wheel

build:
	$(PYTHON) $(SETUP) build

check:
	check-manifest

clean:
	git clean -xfd

dist:
	$(PYTHON) $(SETUP) sdist

distclean: clean

install: build
	$(PYTHON) $(SETUP) install --user

uninstall:
	$(PIP) uninstall -y $(NAME)

test:
	nosetests --with-coverage --cover-package=txrudp --cover-inclusive $(TESTPATH)

wheel: 
	$(PYTHON) $(SETUP) bdist_wheel
