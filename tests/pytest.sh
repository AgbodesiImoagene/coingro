#!/bin/bash

echo "Running Unit tests"

pytest --random-order --ff -x --cov=coingro --cov-config=.coveragerc tests/
