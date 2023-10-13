#!/bin/bash

echo "Running Unit tests"

pytest --ff --random-order --cov=coingro --cov-config=.coveragerc tests/
