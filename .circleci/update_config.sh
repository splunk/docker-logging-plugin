#!/usr/bin/env bash

sudo sed -i -e 's/$SPLUNK_HEC_HOST/'"$SPLUNK_HEC_HOST"'/' /home/circleci/.go_workspace/src/repo/.circleci/functional_tests.sh
sudo sed -i -e 's/$SPLUNK_HEC_TOKEN/'"$SPLUNK_HEC_TOKEN"'/' /home/circleci/.go_workspace/src/repo/.circleci/functional_tests.sh

echo "printing functuonal test script"

cat /home/circleci/.go_workspace/src/repo/.circleci/functional_tests.sh
