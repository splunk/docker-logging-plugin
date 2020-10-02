#!/bin/bash
export SHELL=/bin/bash
set -e

CI_SPLUNK_HOST="${STACK_ID}.stg.splunkcloud.com"
echo "${STACK_ID}" > /workspace/stack_id

git clone https://github.com/splunk/docker-logging-plugin.git

branch=${BRANCH_NAME:-develop}

echo "-----------------run integration tests-----------------"
cd test
pip3 install -r requirements.txt
python3 -m pytest --cache-clear \
   --splunkd-url https://$CI_SPLUNK_HOST:8089 \
   --splunk-user ${CI_SPLUNK_USERNAME} \
   --splunk-password ${CI_SPLUNK_PASSWORD} \
   --splunk-hec-url https://$CI_SPLUNK_HOST:8088 \
   --splunk-hec-token ${SPLUNK_HEC_TOKEN} \
   --docker-plugin-path /workspace/docker-logging-plugin/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
   --fifo-path /workspace/docker-logging-plugin/pipe \
   -p no:warnings
