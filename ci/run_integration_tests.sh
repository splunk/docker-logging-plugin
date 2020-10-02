#!/bin/bash

STACK_ID=`cat target/stack_id`
CI_SPLUNK_HOST="$STACK_ID.stg.splunkcloud.com"

git clone https://github.com/splunk/docker-logging-plugin.git

branch=${BRANCH_NAME:-develop}

echo "Building Docker logging plugin binary.."
cd docker-logging-plugin && git checkout ${branch} && bash make

echo "Start the plugin"
splunk-logging-plugin/rootfs/bin/splunk-logging-plugin


echo "-----------------run integration tests-----------------"
cd test
pip3 install -r requirements.txt
python3 -m pytest --cache-clear \
   --splunkd-url https://$CI_SPLUNK_HOST:8089 \
   --splunk-user admin \
   --splunk-password WhisperAdmin250 \
   --splunk-hec-url https://$CI_SPLUNK_HOST:8088 \
   --splunk-hec-token $SPLUNK_HEC_TOKEN \
   --docker-plugin-path /workspace/docker-logging-plugin/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
   --fifo-path /workspace/docker-logging-plugin/pipe \
   -p no:warnings
