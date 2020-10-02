#! /bin/bash

pip3 install splunk_orca==1.1.0 -i https://repo.splunk.com/artifactory/api/pypi/pypi/simple --upgrade
splunk_orca --version
pip3 install -r test/requirements.txt
STACK_ID=`python3 ci/orca_create_splunk.py`
CI_SPLUNK_HOST="$STACK_ID.stg.splunkcloud.com"
echo "${STACK_ID}" > /build/docker-logging-plugin/ci/stack_id

echo "=============setup splunk HEC=============="

echo "Enable HEC services ..."
curl -X POST -u ${CI_SPLUNK_USERNAME}:${CI_SPLUNK_PASSWORD} -k https://$CI_SPLUNK_HOST:${CI_SPLUNK_PORT}/servicesNS/nobody/splunk_httpinput/data/inputs/http/http/enable

echo "Create new HEC token ..."
curl -X POST -u ${CI_SPLUNK_USERNAME}:${CI_SPLUNK_PASSWORD} -k -d "name=splunk_hec_token&token=${CI_SPLUNK_HEC_TOKEN}" https://$CI_SPLUNK_HOST:${CI_SPLUNK_PORT}/servicesNS/nobody/splunk_httpinput/data/inputs/http

echo "Enable HEC new-token ..."
curl -k -X POST -u ${CI_SPLUNK_USERNAME}:${CI_SPLUNK_PASSWORD} https://$CI_SPLUNK_HOST:${CI_SPLUNK_PORT}/servicesNS/admin/splunk_httpinput/data/inputs/http/splunk_hec_token/enable

echo "Restart Splunk server ..."
curl -k -X POST -u ${CI_SPLUNK_USERNAME}:${CI_SPLUNK_PASSWORD} https://$CI_SPLUNK_HOST:${CI_SPLUNK_PORT}/services/server/control/restart


