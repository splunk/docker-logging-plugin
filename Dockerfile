FROM  golang:1.7

COPY . /go/src/github.com/bbourbie/splunk-log-driver
RUN cd /go/src/github.com/bbourbie/splunk-log-driver && go get && go build --ldflags '-extldflags "-static"' -o /usr/bin/splunk-log-driver
