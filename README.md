# Splunk Log-driver plugin for Docker

Splunk logging plugin allows docker containers to send their logs directly to a Splunk Enterprise service, a Splunk
Cloud deployment, or to a SplunkNova account.

## Getting Started

You need to install Docker Engine >= 1.12.

Additional information about Docker plugins [can be found here.](https://docs.docker.com/engine/extend/plugins_logging/)


### Developing

For development, you can clone and run make

```
git clone git@github.com:splunk/docker-logging-plugin.git
cd docker-logging-plugin
make
```

### Installing

To install the plugin, you can run

```
docker plugin install splunk/docker-logging-driver:latest --alias splunk
docker plugin ls
```

This command will pull and enable the plugin

### Using

The plugin uses the same parameters as the [splunk logging driver](https://docs.docker.com/engine/admin/logging/splunk/).


#### Splunk Enterprise Example

```
$ docker run --log-driver=splunk \
             --log-opt splunk-url=https://your-splunkhost:8088 \
             --log-opt splunk-token=176FCEBF-4CF5-4EDF-91BC-703796522D20 \
             --log-opt splunk-capath=/path/to/cert/cacert.pem \
             --log-opt splunk-caname=SplunkServerDefaultCert \
             --log-opt tag="{{.Name}}/{{.FullID}}" \
             --log-opt labels=location \
             --log-opt env=TEST \
             --env "TEST=false" \
             --label location=west \
             -it ubuntu bash

```

#### SplunkNova Example

Once you make an account on www.splunknova.com, you can grab your API credentials and use them here.

```
$ docker run --log-driver=splunk \
             --log-opt splunk-url=https://api.splunknova.com:443 \
             --log-opt splunk-token=<YOUR BASE64 ENCODED API KEYS> \
             --log-opt splunk-url-path='/v1/events' \
             --log-opt tag="{{.Name}}/{{.FullID}}" \
             --log-opt splunk-format=nova \
             --log-opt splunk-verify-connection=false \
             --log-opt splunk-source='docker-logging' \
             -it ubuntu bash
```

