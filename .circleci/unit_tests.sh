#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

mkdir /home/circleci/.go_workspace/bin
curl https://raw.githubusercontent.com/golang/dep/master/install.sh | sh
dep ensure

echo "Running Golang unit tests..."

go get github.com/Sirupsen/logrus
go get github.com/docker/docker/api/types/plugins/logdriver
go get github.com/docker/docker/daemon/logger
go get github.com/docker/docker/daemon/logger/jsonfilelog
go get github.com/docker/docker/daemon/logger/loggerutils
go get github.com/docker/docker/pkg/ioutils
go get github.com/docker/docker/pkg/urlutil
go get github.com/docker/go-plugins-helpers/sdk
go get github.com/gogo/protobuf/io
go get github.com/pkg/errors
go get github.com/tonistiigi/fifo

go test
