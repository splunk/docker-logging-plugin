#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

mkdir /home/circleci/.go_workspace/bin
curl https://raw.githubusercontent.com/golang/dep/master/install.sh | sh
dep ensure

echo "Running Golang unit tests..."

go test
