#!/bin/bash

echo "Running Unit tests"

pytest -x --ff --random-order --cov=coingro --cov-config=.coveragerc tests/
