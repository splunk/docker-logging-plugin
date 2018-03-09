#!/usr/bin/env bash
export SHELL=/bin/bash
cd /go/docker-logging-plugin

go get -t -v ./...
make
sleep 5


./plugin/rootfs/bin/splunk-log-plugin &
nodejs run.js

echo "send kill signal"

curl -u admin:changeme -k https://splunk-hec:8089/servicesNS/nobody/launcher/configs/conf-inputs -d 'name=batch:///Test-input' > /dev/null 2>&1
