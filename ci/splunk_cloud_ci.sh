#! /bin/bash

pip3 install splunk_orca==1.1.0 -i https://repo.splunk.com/artifactory/api/pypi/pypi/simple --upgrade
splunk_orca --version
pip3 install -r test/requirements.txt
STACK_ID=`python3 ci/orca_create_splunk.py`
CI_SPLUNK_HOST="$STACK_ID.stg.splunkcloud.com"

echo "============= setup splunk HEC =============="

echo "Enable HEC services ..."
curl -X POST -u ${CI_SPLUNK_USERNAME}:${CI_SPLUNK_PASSWORD} -k https://$CI_SPLUNK_HOST:${CI_SPLUNK_PORT}/servicesNS/nobody/splunk_httpinput/data/inputs/http/http/enable

echo "Create new HEC token ..."
curl -X POST -u ${CI_SPLUNK_USERNAME}:${CI_SPLUNK_PASSWORD} -k -d "name=splunk_hec_token&token=${CI_SPLUNK_HEC_TOKEN}" https://$CI_SPLUNK_HOST:${CI_SPLUNK_PORT}/servicesNS/nobody/splunk_httpinput/data/inputs/http

echo "Enable HEC new-token ..."
curl -k -X POST -u ${CI_SPLUNK_USERNAME}:${CI_SPLUNK_PASSWORD} https://$CI_SPLUNK_HOST:${CI_SPLUNK_PORT}/servicesNS/admin/splunk_httpinput/data/inputs/http/splunk_hec_token/enable

echo "Restart Splunk server ..."
curl -k -X POST -u ${CI_SPLUNK_USERNAME}:${CI_SPLUNK_PASSWORD} https://$CI_SPLUNK_HOST:${CI_SPLUNK_PORT}/services/server/control/restart

echo "----------------- update docker file ENV -----------------"

sed -i "s/ENV CI_SPLUNK_USERNAME=/ENV CI_SPLUNK_USERNAME=${CI_SPLUNK_USERNAME}/g" /build/docker-logging-plugin/ci/Dockerfile.docker-plugin
sed -i "s/ENV CI_SPLUNK_PASSWORD=/ENV CI_SPLUNK_PASSWORD=${CI_SPLUNK_PASSWORD}/g" /build/docker-logging-plugin/ci/Dockerfile.docker-plugin
sed -i "s/ENV SPLUNK_HEC_TOKEN=/ENV SPLUNK_HEC_TOKEN=${SPLUNK_HEC_TOKEN}/g" /build/docker-logging-plugin/ci/Dockerfile.docker-plugin
sed -i "s/ENV BRANCH_NAME=/ENV BRANCH_NAME=${BRANCH_NAME}/g" /build/docker-logging-plugin/ci/Dockerfile.docker-plugin
sed -i "s/ENV STACK_ID=/ENV STACK_ID=${STACK_ID}/g" /build/docker-logging-plugin/ci/Dockerfile.docker-plugin


echo "Building Docker logging plugin binary.."
cd /build/docker-logging-plugin && git checkout ${branch} && make

echo "Start the plugin"
splunk-logging-plugin/rootfs/bin/splunk-logging-plugin
