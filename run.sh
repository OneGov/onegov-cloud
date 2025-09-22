#!/bin/bash

export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"

# Run all the failing tests in parallel
venv/bin/python -m pytest \
  tests/onegov/pas/test_parliamentarian_permissions.py::test_view_dashboard_as_parliamentarian \
  tests/onegov/pas/test_app.py::test_app_custom \
  tests/onegov/pas/test_personal_vs_other_access.py::test_parliamentarian_cannot_edit_other_attendance \
  tests/onegov/pas/test_personal_vs_other_access.py::test_commission_president_cannot_edit_other_commission_attendance \
  tests/onegov/pas/test_personal_vs_other_access.py::test_parliamentarian_cannot_view_other_parliamentarian_details \
  tests/onegov/pas/test_views.py::test_copy_rate_set \
  tests/onegov/pas/test_views.py::test_simple_attendence_add \
  tests/onegov/pas/test_parliamentarian_permissions.py::test_view_dashboard_as_commission_president \
  tests/onegov/pas/test_views.py::test_views_manage \
  -v -n auto --dist worksteal
