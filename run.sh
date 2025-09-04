#!/bin/bash
export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"

# Run pytest and mypy as fast as possible 
# Start both, and use multiple mypy processes per directory

pytest -n auto \
  tests/onegov/pas/test_views.py::test_views_manage \
  tests/onegov/pas/test_app.py::test_app_custom \
  tests/onegov/pas/test_dashboard_view.py::test_view_dashboard_as_parliamentarian &

# Capture pytest PID if you want to wait later
PYTEST_PID=$!

mypy src/onegov/pas

# Wait for pytest to finish if needed
wait $PYTEST_PID
