#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

echo "Running functional tests..."



# Start the plugin
sudo splunk-logging-plugin/rootfs/bin/splunk-logging-plugin &


echo "Creating virtual env to run functional tests..."
cd test
curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
apt-get update
apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev git
export PATH="~/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv install --verbose 3.7.0
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

