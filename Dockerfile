FROM  golang:1.19.0

WORKDIR /go/src/github.com/splunk/splunk-logging-plugin/

COPY . /go/src/github.com/splunk/splunk-logging-plugin/

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /bin/splunk-logging-plugin .

FROM alpine:3.7
RUN apk --no-cache add ca-certificates
COPY --from=0 /bin/splunk-logging-plugin /bin/
WORKDIR /bin/
ENTRYPOINT [ "/bin/splunk-logging-plugin" ]
