#!/usr/bin/env bash
set -euo pipefail

./.buildkite/cat .buildkite/generic-pipeline.yml | buildkite-agent pipeline upload
