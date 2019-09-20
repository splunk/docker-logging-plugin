#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

echo "Running functional tests..."

# Start the plugin
/go/src/github.com/splunk/docker-logging-plugin/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin &

echo "Creating virtual env to run functional tests..."
cd /go/src/github.com/splunk/docker-logging-plugin/test
pip3 install virtualenv
virtualenv --python=python3.5 venv
source venv/bin/activate
pip install -r requirements.txt


python -m pytest \
	--splunkd-url https://splunk-hec:8089 \
	--splunk-user admin \
	--splunk-password changeme \
	--splunk-hec-url https://splunk-hec:8088 \
	--splunk-hec-token 00000000-0000-0000-0000-000000000000 \
	--docker-plugin-path /go/src/github.com/splunk/docker-logging-plugin/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /go/src/github.com/splunk/docker-logging-plugin/pipe