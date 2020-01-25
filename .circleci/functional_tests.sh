#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

echo "Running functional tests..."



# Start the plugin
sudo splunk-logging-plugin/rootfs/bin/splunk-logging-plugin &

echo "Creating virtual env to run functional tests..."
cd test
sudo curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev git
sudo export PATH="~/.pyenv/bin:$PATH"
sudo eval "$(pyenv init -)"
sudo eval "$(pyenv virtualenv-init -)"
sudo pyenv install --verbose 3.7.0
sudo pyenv global 3.7.0
sudo pip install -r requirements.txt


sudo python -m pytest \
	--splunkd-url https://$SPLUNK_HEC_HOST:8089 \
	--splunk-user admin \
	--splunk-password notchangeme \
	--splunkd-url https://$SPLUNK_HEC_HOST:8088 \
	--splunk-hec-token $SPLUNK_HEC_TOKEN \
	--docker-plugin-path /home/circleci/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /home/circleci/repo/pipe
	-p no:warnings -s

