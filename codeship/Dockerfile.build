FROM golang:1.9.2

RUN \
  apt-get update && \
  apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg2 \
    software-properties-common

RUN \
  # Docker APT repository
  curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg  | apt-key add - && \
  add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
    $(lsb_release -cs) \
    stable" && \
  \
  # Node.js APT repository
  curl -sL https://deb.nodesource.com/setup_9.x | bash - && \
  \
  # Basic dependencies
  apt-get update && \
  apt-get install -y --no-install-recommends \
    build-essential \
    docker-ce \
    gcc \
    git \
    nodejs \
    npm \
    python3 \
    python3-dev \
    python3-pip \
    psmisc && \
  apt-get autoclean && \
  apt-get clean && \
  \
  # Node.js dependencies
  npm install --no-save \
    protocol-buffers \
    request && \
  \
  # Python dependencies
  pip3 install virtualenv

RUN mkdir -p /go/src/github.com/splunk/docker-logging-plugin/splunk-logging-plugin/rootfs/bin

WORKDIR /go/src/github.com/splunk/docker-logging-plugin/

COPY . /go/src/github.com/splunk/docker-logging-plugin/

# install go dep
RUN curl https://raw.githubusercontent.com/golang/dep/master/install.sh | sh
RUN cd /go/src/github.com/splunk/docker-logging-plugin && dep ensure

#Build plugin
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o /go/src/github.com/splunk/docker-logging-plugin/splunk-logging-plugin/rootfs/bin/splunk-logging-plugin .
