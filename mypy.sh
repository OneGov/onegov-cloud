#!/usr/bin/env bash
set -euo pipefail

# change to script directory
cd $(dirname "$0")

# make sure virtual env is active
if [ -z "${VIRTUAL_ENV:-}" ]; then
    source venv/bin/activate
fi

echo "Running type checks on onegov package"
mypy -p onegov
echo "Running type checks on do/changes"
mypy do/changes
