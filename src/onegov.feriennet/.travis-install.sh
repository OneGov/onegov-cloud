#!/bin/bash
pip install --upgrade pip
pip install tox

if [ "$TOXENV" = 'py34' ]; then
    pip install coveralls
fi
