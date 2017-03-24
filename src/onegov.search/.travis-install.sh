#!/bin/bash

pip install tox

if [ "$TOXENV" = 'py34' ]; then
    pip install coveralls
fi
