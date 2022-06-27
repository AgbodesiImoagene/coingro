#!/bin/bash

echo "Running Unit tests"

pytest --random-order --cov=coingro --cov-config=.coveragerc tests/
