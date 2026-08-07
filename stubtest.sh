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
echo "Running stubtest on legacy-cgi"
stubtest cgi \
         --mypy-config-file pyproject.toml \
         --allowlist tests/stubtest/cgi_allowlist.txt

echo "Running stubtest on depot"
stubtest depot \
         --mypy-config-file pyproject.toml \
         --allowlist tests/stubtest/depot_allowlist.txt \
         --ignore-missing-stub

echo "Running stubtest on pdfdocument"
stubtest pdfdocument \
         --mypy-config-file pyproject.toml \
         --allowlist tests/stubtest/pdfdocument_allowlist.txt

echo "Running stubtest on purl"
stubtest purl \
         --mypy-config-file pyproject.toml

echo "Running stubtest on sqlalchemy_utils"
stubtest sqlalchemy_utils \
         --mypy-config-file pyproject.toml \
         --allowlist tests/stubtest/sqlalchemy_utils_allowlist.txt \
         --ignore-missing-stub

echo "Running stubtest on transaction"
stubtest transaction \
         --mypy-config-file pyproject.toml \
         --allowlist tests/stubtest/transaction_allowlist.txt

echo "Running stubtest on webcolors"
stubtest webcolors \
         --mypy-config-file pyproject.toml \
         --ignore-missing-stub

echo "Running stubtest on webtest"
stubtest webtest \
         --mypy-config-file pyproject.toml \
         --allowlist tests/stubtest/webtest_allowlist.txt

echo "Running stubtest on wtforms"
stubtest wtforms \
         --mypy-config-file pyproject.toml \
         --allowlist tests/stubtest/wtforms_allowlist.txt

echo "Running stubtest on zope.sqlalchemy"
stubtest zope.sqlalchemy \
         --mypy-config-file pyproject.toml \
         --allowlist tests/stubtest/zope.sqlalchemy_allowlist.txt
