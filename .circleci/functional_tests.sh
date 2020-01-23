#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

echo "Running functional tests..."

# Start the plugin
sudo splunk-logging-plugin/rootfs/bin/splunk-logging-plugin
sleep 30

echo "Creating virtual env to run functional tests..."
pyenv global 3.7.0
cd test
pip3 install virtualenv
virtualenv --python=python3.7 venv
source venv/bin/activate
pip install -r requirements.txt


python -m pytest \
	--splunkd-url https://$CI_SPLUNK_HEC_HOST:8089 \
	--splunk-user admin \
	--splunk-password $CI_SPLUNK_PASSWORD \
	--splunkd-url https://$CI_SPLUNK_HEC_HOST:8088 \
	--splunk-hec-token $CI_SPLUNK_HEC_TOKEN \
	--docker-plugin-path /home/circleci/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /home/circleci/repo/pipe
	-p no:warnings -s

