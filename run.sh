#!/bin/bash

export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"

# Run all tests in parallel
venv/bin/python -m pytest tests/onegov/pas/ -v -n auto --dist worksteal
