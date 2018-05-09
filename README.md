
# What does Splunk Connect for Docker do?
Splunk Connect for Docker is a plug-in that extends and expands Docker's logging capabilities so that customers can push their Docker and container logs to their Splunk on-premise or cloud deployment.

Splunk Connect for Docker is a supported open source product. Customers with an active Splunk support contract receive Splunk Extension support under the Splunk Support Policy, which can be found at https://www.splunk.com/en_us/legal/splunk-software-support-policy.html. 

See the Docker Engine managed plugin system documentation at https://docs.docker.com/engine/extend/ on support for Microsoft Windows and other platforms. See the Prerequisites in this document for more information about system requirements. 

# Prerequisites
Before you install Splunk Connect for Docker, make sure your system meets the following minimum prerequisites:

* Docker Engine: Version 17.05 or later. If you plan to configure Splunk Connect for Docker via 'daemon.json', you must have the Docker Community Edition (Docker-ce) 18.03 equivalent or later installed.
* Splunk Enterprise, Splunk Light, or Splunk Cloud version 6.6 or later. Splunk Connect for Docker plugin is not currently supported on Windows.
* For customers deploying to Splunk Cloud, HEC must be enabled and a token must be generated by Splunk Support before logs can be ingested.
* Configure an HEC token on Splunk Enterprise or Splunk Light (either single instance or distributed environment). Refer to the set up and use HTTP Event Collector documentation for more details.
* Operating System Platform support as defined in Docker Engine managed plugin system documentation.

# Install and configure Splunk Connect for Docker

## Step 1: Get an HTTP Event Collector token
You must configure the Splunk HTTP Event Collector (HEC) to send your Docker container logging data to Splunk Enterprise or Splunk Cloud. HEC uses tokens as an alternative to embedding Splunk Enterprise or Splunk Cloud credentials in your app or supporting files. For more about how the HTTP event collector works, see http://docs.splunk.com/Documentation/Splunk/7.0.3/Data/UsetheHTTPEventCollector

1. Enable your HTTP Event collector:
http://docs.splunk.com/Documentation/Splunk/7.0.3/Data/HECWalkthrough#Enable_HEC
2. Create an HEC token:
http://docs.splunk.com/Documentation/Splunk/7.0.3/Data/UsetheHTTPEventCollector
http://docs.splunk.com/Documentation/Splunk/7.0.3/Data/UseHECusingconffiles

Note the following when you generate your token:
* Make sure that indexer acknowledgement is disabled for your token. 
* Optionally, enable the indexer acknowledgement functionality by clicking the Enable indexer management checkbox. 
* Do not generate your token using the default TLS cert provided by Splunk. The default certificates are not secure. For information about configuring Splunk to use self-signed or third-party certs, see http://docs.splunk.com/Documentation/Splunk/7.0.3/Security/AboutsecuringyourSplunkconfigurationwithSSL.
* Splunk Cloud customers must file a support request in order to have a token generated.

## Step 2: Install the plugin 
There are multiple ways to install Splunk Connect for Docker, Splunk recommends installing from Docker Store (option 1) to ensure the most current and stable build.

### Install the Plugin from Docker Store

1. Pull the plugin from docker hub
```
$ docker plugin install splunk/docker-logging-plugin:latest --alias splunk-logging-plugin
```
2. Enable the plugin if needed:
```
$ docker plugin enable splunk-logging-plugin
```
### Install the plugin from the tar file 

1. Clone the repository and check out release branch
```
$ git clone  https://github.com/splunk/docker-logging-plugin.git
```
2. Create the plugin package
```
$ cd docker-logging-plugin
$ make package # this creates a splunk-logging-plugin.tar.gz
```
3. unzip the package
```
$ tar -xzf splunk-logging-plugin.tar.gz
```
4. Create the plugin
```
$ docker plugin create splunk-logging-plugin:latest splunk-logging-plugin/
```
5. Verify that the plugin is installed by running the following command:
```
$ docker plugin ls
```
6. Enable the plugin
```
$ docker plugin enable splunk-logging-plugin:latest
```
## Step 3: Run containers with the plugin installed

Splunk Connect for Docker continually listens for logs, but your containers must also be running so that the container logs are forwarded to Splunk Connect for Docker. The following examples describe how to configure containers to run with Splunk Connect for Docker. 

To start your containers, refer to the Docker Documentation found at: 

https://docs.docker.com/config/containers/logging/configure/  
https://docs.docker.com/config/containers/logging/configure/#configure-the-delivery-mode-of-log-messages-from-container-to-log-driver 

## Examples

This sample <addr>daemon.json</addr> command configures Splunk Connect for Docker for all containers on the docker engine. Splunk Software recommends that when working in a production environment, you pass your HEC token through <addr>daemon.json</addr> as opposed to the command line.
```
{
  "log-driver": "splunk-logging-plugin",
  "log-opts": {
    "splunk-url": "<splunk_hec_endpoint>",
    "splunk-token": "<splunk-hec-token>",
    "splunk-insecureskipverify": "true"
  }
}
```
This sample command configures Splunk Connect for Docker for a single container.
```
$ docker run --log-driver=splunk-logging-plugin --log-opt splunk-url=<splunk_hec_endpoint> --log-opt splunk-token=<splunk-hec_token> --log-opt splunk-insecureskipverify=true -d <docker_image>
```
## Step 4: Set Configuration variables

Use the configuration variables to configure the behaviors and rules for Splunk Connect for Docker. For example you can confiugre your certificate security or how messages are formatted and distributed. Note the following:

* Configurations that pass though docker <addr>run --log-opt <opt><addr> are effective instantaneously. 
* You must restart the Docker engine after configuring through `<addr>`daemon.json`<addr>` 
	
### How to use the variables

The following is an example of the logging options specified for the Splunk Enterprise instance. In this example:

The path to the root certificate and Common Name is specified using an HTTPS scheme to be used for verification. 
```
$ docker run --log-driver=splunk-logging-plugin\
             --log-opt splunk-token=176FCEBF-4CF5-4EDF-91BC-703796522D20 \
             --log-opt splunk-url=https://splunkhost:8088 \
             --log-opt splunk-capath=/path/to/cert/cacert.pem \
             --log-opt splunk-caname=SplunkServerDefaultCert \
             --log-opt tag="{{.Name}}/{{.FullID}}" \
             --log-opt labels=location \
             --log-opt env=TEST \
             --env "TEST=false" \
             --label location=west \
             <docker_image>
```
### Required Variables

Variable | Description 
------------ | -------------	
splunk-token | Splunk HTTP Event Collector token.
splunk-url | Path to your Splunk Enterprise, self-service Splunk Cloud instance, or Splunk Cloud managed cluster (including port and scheme used by HTTP Event Collector) in one of the following formats: https://your_splunk_instance:8088 or https://input-prd-p-XXXXXXX.cloud.splunk.com:8088 or https://http-inputs-XXXXXXXX.splunkcloud.com


### Optional Variables

Variable | Description | Default
------------ | ------------- | -------------
splunk-source | Event source |	
splunk-sourcetype  | Event source type | 
splunk-index | Event index. (Note that HEC token must be configured to accept the specified index) | 	
splunk-capath | Path to root certificate. (Must be specified if splunk-insecureskipverify is false) | 
splunk-caname | Name to use for validating server certificate; by default the hostname of the splunk-url is used. | 	
splunk-insecureskipverify| "false" means that the service certificates are validated and "true" means that server certificates are not validated. | false
splunk-format | Message format. Values can be inline, json, or raw. For more infomation about formats see the Messageformats option. | inline
splunk-verify-connection| Upon plug-in startup, verify that Splunk Connect for Docker can connect to Splunk HEC endpoint. False indicates that Splunk Connect for Docker will start up and continue to try to connect to HEC and will push logs to buffer until connection has been establised. Logs will roll off buffer once buffer is full. True indicates that Splunk Connect for Docker will not start up if connection to HEC cannot be established. | false
splunk-gzip | Enable/disable gzip compression to send events to Splunk Enterprise or Splunk Cloud instance. | false
splunk-gzip-level | Set compression level for gzip. Valid values are -1 (default), 0 (no compression), 1 (best speed) … 9 (best compression). | -1
tag | Specify tag for message, which interpret some markup. Refer to the log tag option documentation for customizing the log tag format. https://docs.docker.com/v17.09/engine/admin/logging/log_tags/	| {{.ID}} (12 characters of the container ID)
labels | Comma-separated list of keys of labels, which should be included in message, if these labels are specified for container. | 	
env | Comma-separated list of keys of environment variables to be included in message if they specified for a container. | 	
env-regex | A regular expression to match logging-related environment variables. Used for advanced log tag options. If there is collision between the label and env keys, the value of the env takes precedence. Both options add additional fields to the attributes of a logging message. | 	


### Advanced options - Environment Variables

To overwrite these values through environment variables, use docker plugin set <env>=<value>. For more information, see https://docs.docker.com/engine/reference/commandline/plugin_set/ .

Variable | Description | Default
------------ | ------------- | -------------
SPLUNK_LOGGING_DRIVER_POST_MESSAGES_FREQUENCY | How often plug-in posts messages when there is nothing to batch, i.e., the maximum time to wait for more messages to batch. The internal buffer used for batching is flushed either when the buffer is full (the disgnated batch size is reached) or the buffer timesout (specified by this frequency) | 5s
SPLUNK_LOGGING_DRIVER_POST_MESSAGES_BATCH_SIZE | The number of messages the plug-in should collect before sending them in one batch. | 	1000	
SPLUNK_LOGGING_DRIVER_BUFFER_MAX | The maximum amount of messages to hold in buffer and retry when the plug-in cannot connect to remote server. |  10 * 1000
SPLUNK_LOGGING_DRIVER_CHANNEL_SIZE | How many pending messages can be in the channel used to send messages to background logger worker, which batches them. | 4 * 1000
SPLUNK_LOGGING_DRIVER_TEMP_MESSAGES_HOLD_DURATION | Appends logs that are chunked by docker with 16kb limit. It specifies how long the system can wait for the next message to come. | 100ms 
SPLUNK_LOGGING_DRIVER_TEMP_MESSAGES_BUFFER_SIZE	| Appends logs that are chunked by docker with 16kb limit. It specifies the biggest message in bytes that the system can reassemble. The value provided here should be smaller than or equal to the Splunk HEC limit. 1 MB is the default HEC setting. | 1048576 (1mb)


### Message formats
There are three logging plug-in messaging formats set under the optional variable splunk-format:

* inline (this is the default format) 
* json
* raw

The default format is inline, where each log message is embedded as a string and is assigned to "line" field. For example:
```
// Example #1
{
    "attrs": {
        "env1": "val1",
        "label1": "label1"
    },
    "tag": "MyImage/MyContainer",
    "source":  "stdout",
    "line": "my message"
}

// Example #2
{
    "attrs": {
        "env1": "val1",
        "label1": "label1"
    },
    "tag": "MyImage/MyContainer",
    "source":  "stdout",
    "line": "{\"foo\": \"bar\"}"
}
```
When messages are JSON objects, you may want to embed them in the message sent to Splunk.

To format messages as json objects, set --log-opt splunk-format=json. The plug-in will try to parse every line as a JSON object and embed the json object to "line" field. If it cannot parse the message, it is sent inline. For example:
```
//Example #1
{
    "attrs": {
        "env1": "val1",
        "label1": "label1"
    },
    "tag": "MyImage/MyContainer",
    "source":  "stdout",
    "line": "my message"
}

//Example #2
{
    "attrs": {
        "env1": "val1",
        "label1": "label1"
    },
    "tag": "MyImage/MyContainer",
    "source":  "stdout",
    "line": {
        "foo": "bar"
    }
}
```
If --log-opt splunk-format=raw, each message together with attributes (environment variables and labels) and tags are combined in a raw string. Attributes and tags are prefixed to the message. For example:
```
MyImage/MyContainer env1=val1 label1=label1 my message
MyImage/MyContainer env1=val1 label1=label1 {"foo": "bar"}
```
# Troubleshooting

If your Splunk Connector for Docker does not behave as expected, use the debug functionality and then refer to the following tips included in output.

## Enable Debug Mode to find log errors

Plugin logs can be found as docker daemon log. To enable debug mode, export environment variable LOGGIN_LEVEL=DEBUG in docker engine environment. See the Docker documentation for information about how to enable debug mode in your docker environment: https://docs.docker.com/config/daemon/

## Use the debugger to check your debug the Splunk HEC connection

Check HEC endpoint accessibility Docker environment. If the endpoint cannot be reached, debug logs are not sent to Splunk, or the logs or will buffer and drop as they roll off the buffer. 
```
Test HEC endpoint is accessible
$ curl -k https://<ip_address>:8088/services/collector/health
{"text":"HEC is healthy","code":200}
```
## Check your HEC configuration for clusters

If you are using an Indexer Cluster, the current plugin accepts a single splunk-url value. We recommend that you configure a load balancer in front of your Indexer tier. Make sure the load balancer can successfully tunnel the HEC requests to the indexer tier. If HEC is configured in an Indexer Cluster environment, all indexers should have same HEC token configured. See http://docs.splunk.com/Documentation/Splunk/7.0.3/Data/UsetheHTTPEventCollector.  

## Check your heavy forwarder connection

If you ae using a heavy forwarder to preprocess the events (e.g: funnel multiple log lines to a single event), make sure that the heavy forwarder is properly connecting to the indexers. To troubleshoot the forwarder and receiver connection, see: https://docs.splunk.com/Documentation/SplunkCloud/7.0.0/Forwarding/Receiverconnection. 

## Check the plugin's debug log in docker

Stdout of a plugin is redirected to Docker logs. Such entries have a plugin=<ID> suffix.

To find out the plugin ID of Splunk Connect for Docker, use the command below and look for Splunk Logging Plugin entry.
```
# list all the plugins
$ docker plugin ls
```
Depending on your system, location of Docker daemon logging may vary.  Refer to Docker documentation for Docker daemon log location for your specific platform. Here are a few examples:

* Ubuntu (old using upstart ) - /var/logging/upstart/docker.logging
* Ubuntu (new using systemd ) - sudo journalctl -fu docker.service
* Boot2Docker - /var/logging/docker.logging
* Debian GNU/Linux - /var/logging/daemon.logging
* CentOS - /var/logging/daemon.logging | grep docker
* CoreOS - journalctl -u docker.service
* Fedora - journalctl -u docker.service
* Red Hat Enterprise Linux Server - /var/logging/messages | grep docker
* OpenSuSE - journalctl -u docker.service
* OSX - ~/Library/Containers/com.docker.docker/Data/com.docker.driver.amd64-linux/logging/d‌ocker.logging
* Windows - Get-EventLog -LogName Application -Source Docker -After (Get-Date).AddMinutes(-5) | Sort-Object Time, as mentioned here.
	
