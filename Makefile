TESTPATH=./tests

.PHONY: all test unittest

all: test

test: unittest

unittest:
	nosetests --with-coverage --cover-package=txrudp --cover-inclusive $(TESTPATH)
