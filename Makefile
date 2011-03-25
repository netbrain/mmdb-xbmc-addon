# Makefile dishonorably stolen from pygments

PYTHON ?= python

export PYTHONPATH = $(shell echo "$$PYTHONPATH"):$(shell python -c 'import os; print ":".join(os.path.abspath(line.strip()) for line in file("PYTHONPATH"))' 2>/dev/null)

.PHONY: all clean test test-coverage

all: clean test


clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	-rm -f coverage.xml
	-rm -f nosetests.xml
test:
	nosetests --with-xunit

test-coverage:
	coverage xml --omit="/usr/*","tests/*"
