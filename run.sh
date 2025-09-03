#!/bin/bash
export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"

# Run tests in parallel using GNU parallel
parallel --jobs $(nproc) pytest {} ::: \
  tests/onegov/pas/test_views.py::test_views_manage \
  tests/onegov/pas/test_app.py::test_app_custom \
  tests/onegov/pas/test_dashboard_view.py::test_view_dashboard_as_parliamentarian

# Run mypy in parallel using xargs
find src/onegov/pas -name "*.py" | \
  xargs -P $(nproc) -I{} sh -c 'echo "Checking {}"; mypy {}'
