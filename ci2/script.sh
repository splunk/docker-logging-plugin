#!/usr/bin/env bash
export SHELL=/bin/bash
cd /go/docker-logging-plugin

go get -t -v ./...
make
sleep 30


./plugin/rootfs/bin/splunk-log-plugin &
nodejs run.js


tail -f /dev/null