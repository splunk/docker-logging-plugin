FROM  golang:1.9.2

WORKDIR /go/src/github.com/splunk/splunk-logging-plugin/

COPY . /go/src/github.com/splunk/splunk-logging-plugin/

# install glide
RUN curl https://glide.sh/get | sh

RUN cd /go/src/github.com/splunk/splunk-logging-plugin && glide install

RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /bin/splunk-logging-plugin .

FROM alpine:3.7
RUN apk --no-cache add ca-certificates
COPY --from=0 /bin/splunk-logging-plugin /bin/
WORKDIR /bin/
ENTRYPOINT [ "/bin/splunk-logging-plugin" ]
