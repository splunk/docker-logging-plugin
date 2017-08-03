# Splunk log driver

Splunk log driver is a docker plugin that allows docker containers to send its logs directly to a Splunk driver.

## Getting Started

You can build this project whereever Docker engine is installed to a pretty recent version (>1.3). 
Please, have a look at [Docker plugin documentation](https://docs.docker.com/engine/extend/#debugging-plugins)


### Prerequisites

So, you need install on your machine 

```
docker
make
```

### Compiling and Installing

To compile and install the plugin driver, just run 

```
make && make enable
```

This command will pull the docker image and build the new docker image and extract the plugin. 


### Running a docker image

The plugin is using the same parameters as the splunk driver, please have a look at [splunk driver documentation](https://docs.docker.com/engine/admin/logging/splunk/) 
to know what parameters to use

```
$ docker run --log-driver=splunk-log-driver:next \
           --log-opt splunk-token=176FCEBF-4CF5-4EDF-91BC-703796522D20 \
           --log-opt splunk-url=https://splunkhost:8088 \
           --log-opt splunk-capath=/path/to/cert/cacert.pem \
           --log-opt splunk-caname=SplunkServerDefaultCert \
           --log-opt tag="{{.Name}}/{{.FullID}}" \
           --log-opt labels=location \
           --log-opt env=TEST \
           --env "TEST=false" \
           --label location=west \
       your/application

```
