#!/bin/bash

export JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"

# Run all tests in parallel
#venv/bin/python -m pytest tests/onegov/pas/ -v -n auto --dist worksteal

venv/bin/python -m pytest tests/onegov/pas/test_personal_vs_other_access.py::test_attendance_collection_shows_only_own_records tests/onegov/pas/test_personal_vs_other_access.py::test_parliamentarian_cannot_view_other_parliamentarian_details tests/onegov/pas/test_parliamentarian_permissions.py::test_view_files_collection -n auto
