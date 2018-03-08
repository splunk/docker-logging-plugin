#!/usr/bin/env bash
export SHELL=/bin/bash
cd /go

go get -t -v ./...
cd docker-logging-plugin
make
sleep 30


./plugin/rootfs/bin/splunk-log-plugin &
nodejs run.js


tail -f /dev/null