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
	--splunkd-url https://localhost:8089 \
	--splunk-user admin \
	--splunk-password #{ENV['SPLUNK_PASSWORD']} \
	--splunk-hec-url #{ENV['SPLUNK_HEC_HOST']}:8088 \
	--splunk-hec-token #{ENV['SPLUNK_HEC_TOKEN']} \
	--docker-plugin-path /go/src/github.com/splunk/docker-logging-plugin/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /go/src/github.com/splunk/docker-logging-plugin/pipe