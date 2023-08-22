#!/usr/bin/env bash
set -euo pipefail

# change to script directory
cd $(dirname "$0")

# make sure virtual env is active unless specifically turned off
if [[ -z "${VIRTUAL_ENV:-}" && "${SKIP_VENV:-}" -ne "1" ]]; then
    source venv/bin/activate
fi

# most of our stubs are incomplete so we pass --ignore-missing-stub
# whenever a package hasn't been fully stubbed out
echo "Running stubtest on dectate"
stubtest dectate --mypy-config-file pyproject.toml \
                 --allowlist tests/stubtest/dectate_allowlist.txt \
                 --ignore-missing-stub

echo "Running stubtest on depot"
stubtest depot --mypy-config-file pyproject.toml \
               --allowlist tests/stubtest/depot_allowlist.txt \
               --ignore-missing-stub

echo "Running stubtest on morepath"
stubtest morepath --mypy-config-file pyproject.toml \
                  --allowlist tests/stubtest/morepath_allowlist.txt \
                  --ignore-missing-stub

echo "Running stubtest on reg"
stubtest reg --mypy-config-file pyproject.toml \
             --ignore-missing-stub

echo "Running stubtest on webcolors"
stubtest webcolors --mypy-config-file pyproject.toml \
                   --ignore-missing-stub

echo "Running stubtest on wtforms"
stubtest wtforms --mypy-config-file pyproject.toml \
                 --allowlist tests/stubtest/wtforms_allowlist.txt
