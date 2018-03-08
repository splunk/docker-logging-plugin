FROM golang:1.10.0

# Install packages
RUN apt-get update && \
    apt-get install -y \
        vim \
        jq \
        curl \
        git \
        #python \
        gcc \
        #python-dev \
        #CLI driven testing tool for python
        #python-tox \
        apt-transport-https \
        ca-certificates \
        gnupg2 \
        software-properties-common && \
        apt-get autoclean \
        apt-get clean

RUN curl -sL https://deb.nodesource.com/setup_9.x | bash -
RUN apt-get install -y nodejs
RUN apt-get install -y npm
RUN npm install protocol-buffers request --save


# Install prerequisites, configure Docker apt repositories and install the latest Docker CE binaries(https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce)
RUN curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg > /tmp/dkey; apt-key add /tmp/dkey && \
add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
   $(lsb_release -cs) \
   stable" && \
apt-get update && \
apt-get -y install docker-ce

ENV GOPATH=/go

# Go tools
#RUN go get github.com/rancher/trash
#RUN go get github.com/golang/lint/golint

WORKDIR /go

RUN git clone https://github.com/luckyj5/docker-logging-plugin.git

COPY ci2/script.sh /go/docker-logging-plugin
COPY ci2/run.js /go/docker-logging-plugin
RUN chmod +x /go/docker-logging-plugin/script.sh
RUN chmod +x /go/docker-logging-plugin/run.js


CMD ["/bin/sh", "-c", "/go/docker-logging-plugin/script.sh"]
