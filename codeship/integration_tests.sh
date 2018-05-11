#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

echo "Running integration tests..."

# Start the Docker plugin
/go/src/github.com/splunk/docker-logging-plugin/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin &

nodejs /go/src/github.com/splunk/docker-logging-plugin/codeship/integration/run.js
