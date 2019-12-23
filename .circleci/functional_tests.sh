#!/usr/bin/env bash
export SHELL=/bin/bash

set -e


echo "Creating virtual env to run functional tests..."
cd test
pip3 install virtualenv
virtualenv --python=python3.7 venv
source venv/bin/activate
pip install -r requirements.txt


python -m pytest \
	--splunkd-url https://localhost:8089 \
	--splunk-user admin \
	--splunk-password changeme \
	--splunk-hec-url http://localhost:8088 \
	--splunk-hec-token 2160C7EF-2CE9-4307-A180-F852B99CF417 \
	--docker-plugin-path /Users/gpatzlaff/Code/docker/update-tests/docker-logging-plugin/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /Users/gpatzlaff/Code/docker/update-tests/docker-logging-plugin/pipe