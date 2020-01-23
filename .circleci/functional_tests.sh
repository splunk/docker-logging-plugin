#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

echo "Running functional tests..."

# Start the plugin
splunk-logging-plugin/rootfs/bin/splunk-logging-plugin &

echo "Creating virtual env to run functional tests..."
cd test
pyenv global 3.7.0
pip3 install virtualenv
virtualenv --python=python3.7 venv
source venv/bin/activate
pip install -r requirements.txt


python -m pytest \
	--splunkd-url https://54.183.32.171:8089 \
	--splunk-user admin \
	--splunk-password changeme \
	--splunk-hec-url https://54.183.32.171:8088 \
	--splunk-hec-token 029a2c72-e8e7-4b8e-9d1d-4ddf4b6f229e \
	--docker-plugin-path /home/circleci/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /home/circleci/repo/pipe
