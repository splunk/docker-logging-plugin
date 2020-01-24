#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

echo "Running functional tests..."



# Start the plugin
sudo splunk-logging-plugin/rootfs/bin/splunk-logging-plugin &


echo "Creating virtual env to run functional tests..."
cd test
pyenv global 3.7.0
pip install -r requirements.txt


python -m pytest \
	--splunkd-url https://$SPLUNK_HEC_HOST:8089 \
	--splunk-user admin \
	--splunk-password notchangeme \
	--splunkd-url https://$SPLUNK_HEC_HOST:8088 \
	--splunk-hec-token $SPLUNK_HEC_TOKEN \
	--docker-plugin-path /home/circleci/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /home/circleci/repo/pipe
	-p no:warnings -s

