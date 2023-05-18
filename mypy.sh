#!/usr/bin/env bash
set -euo pipefail

# change to script directory
cd $(dirname "$0")

# make sure virtual env is active
if [ -z "${VIRTUAL_ENV:-}" ]; then
    source venv/bin/activate
fi

mypy -p onegov
