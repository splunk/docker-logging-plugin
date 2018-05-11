#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

echo "Running Golang unit tests..."

go test
