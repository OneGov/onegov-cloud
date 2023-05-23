#!/usr/bin/env bash
set -euo pipefail

./.buildkite/cat .buildkite/container-pipeline.yml | buildkite-agent pipeline upload
