#!/bin/bash

COUNT=0
output=$(curl -s -u admin:notchangeme -k https://localhost:8089/services/server/info/server-info?output_mode=json | jq -r ".entry[0].content.health_info")

while [ "$output" != "green" ] && [ $COUNT -lt 12 ]
do
    echo "Waiting for Splunk to be ready (iteration $COUNT)..."
    sleep 10
    output=$(curl -s -u admin:notchangeme -k https://localhost:8089/services/server/info/server-info?output_mode=json | jq -r ".entry[0].content.health_info")
    ((COUNT=COUNT+1))
done

if [ "$output" = "green" ] ; then
    echo "Splunk now ready."
else
    echo "Failed waiting for Splunk"
    exit 1
fi
