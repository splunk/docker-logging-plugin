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
	--splunkd-url https://127.0.0.1:8089 \
	--splunk-user admin \
	--splunk-password helloworld \
	--splunk-hec-url https://127.0.0.1:8088 \
	--splunk-hec-token a6b5e77f-d5f6-415a-bd43-930cecb12959 \
	--docker-plugin-path /home/circleci/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /home/circleci/repo/pipe
