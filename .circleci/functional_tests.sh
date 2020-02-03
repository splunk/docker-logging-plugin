#!/usr/bin/env bash
export SHELL=/bin/bash

set -e

echo "Running functional tests..."

#sudo su

# Start the plugin
sudo /home/circleci/.go_workspace/src/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin &
rm -rf /opt/circleci/.pyenv
echo "Creating virtual env to run functional tests..."
cd test
curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash
sudo apt-get update
sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev git
export PATH="~/.pyenv/bin:$PATH"
pyenv install 3.7.0
pyenv global 3.7.0


sudo pip install --upgrade pip
pip install virtualenv
virtualenv --python=python3.5 venv
source venv/bin/activate
pip install -r requirements.txt
deactivate

#Run functional tests from within virtualenv
sudo venv/bin/python -m pytest --cache-clear \
   --splunkd-url https://$SPLUNK_HEC_HOST:8089 \
   --splunk-user admin \
   --splunk-password notchangeme \
   --splunk-hec-url https://$SPLUNK_HEC_HOST:8088 \
   --splunk-hec-token $SPLUNK_HEC_TOKEN \
   --docker-plugin-path /home/circleci/.go_workspace/src/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
   --fifo-path /home/circleci/.go_workspace/src/repo/pipe \
   -p no:warnings  partial_log/test_partial_log.py::test_partial_log

sudo venv/bin/python -m pytest --cache-clear \
   --splunkd-url https://$SPLUNK_HEC_HOST:8089 \
   --splunk-user admin \
   --splunk-password notchangeme \
   --splunk-hec-url https://$SPLUNK_HEC_HOST:8088 \
   --splunk-hec-token $SPLUNK_HEC_TOKEN \
   --docker-plugin-path /home/circleci/.go_workspace/src/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
   --fifo-path /home/circleci/.go_workspace/src/repo/pipe \
   -p no:warnings  partial_log/test_partial_log.py::test_partial_log_flush_timeout

sudo venv/bin/python -m pytest --cache-clear \
   --splunkd-url https://$SPLUNK_HEC_HOST:8089 \
   --splunk-user admin \
   --splunk-password notchangeme \
   --splunk-hec-url https://$SPLUNK_HEC_HOST:8088 \
   --splunk-hec-token $SPLUNK_HEC_TOKEN \
   --docker-plugin-path /home/circleci/.go_workspace/src/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
   --fifo-path /home/circleci/.go_workspace/src/repo/pipe \
   -p no:warnings  partial_log/test_partial_log.py::test_partial_log_flush_size_limit

sudo venv/bin/python -m pytest --cache-clear \
   --splunkd-url https://$SPLUNK_HEC_HOST:8089 \
   --splunk-user admin \
   --splunk-password notchangeme \
   --splunk-hec-url https://$SPLUNK_HEC_HOST:8088 \
   --splunk-hec-token $SPLUNK_HEC_TOKEN \
   --docker-plugin-path /home/circleci/.go_workspace/src/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
   --fifo-path /home/circleci/.go_workspace/src/repo/pipe \
   -p no:warnings  malformed_data

sudo venv/bin/python -m pytest --cache-clear \
   --splunkd-url https://$SPLUNK_HEC_HOST:8089 \
   --splunk-user admin \
   --splunk-password notchangeme \
   --splunk-hec-url https://$SPLUNK_HEC_HOST:8088 \
   --splunk-hec-token $SPLUNK_HEC_TOKEN \
   --docker-plugin-path /home/circleci/.go_workspace/src/repo/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
   --fifo-path /home/circleci/.go_workspace/src/repo/pipe \
   -p no:warnings  config_params

