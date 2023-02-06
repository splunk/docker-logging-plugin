#!/bin/bash

COUNT=0
output=$(curl -s -u admin:notchangeme -k https://localhost:8089/services/server/info/server-info?output_mode=json | jq -r ".entry[0].content.kvStoreStatus")

while [ "$output" != "ready" ] && [ $COUNT -lt 12 ]
do
    echo "Waiting for Splunk to be ready (iteration $COUNT)..."
    sleep 10
    output=$(curl -s -u admin:notchangeme -k https://localhost:8089/services/server/info/server-info?output_mode=json | jq -r ".entry[0].content.kvStoreStatus")
    ((COUNT=COUNT+1))
done

if [ "$output" = "ready" ] ; then
    echo "Splunk now ready."
else
    echo "Failed waiting for Splunk"
    exit 1
fi
