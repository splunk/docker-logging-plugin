FROM mlaccetti/docker-oracle-java8-ubuntu-16.04

ENV SPLUNK_PRODUCT=splunk \
    SPLUNK_VERSION=7.0.2 \
    SPLUNK_BUILD=03bbabbd5c0f \
    SPLUNK_HOME=/opt/splunk \
    SPLUNK_GROUP=splunk \
    SPLUNK_USER=splunk

ENV SPLUNK_FILENAME=splunk-${SPLUNK_VERSION}-${SPLUNK_BUILD}-Linux-x86_64.tgz

# Set WORKDIR to Splunks home directory
RUN mkdir -p ${SPLUNK_HOME}
WORKDIR ${SPLUNK_HOME}
VOLUME [ "/opt/splunk/var" ]

# Ports Splunk Web, Splunk Daemon, KVStore, Splunk Indexing Port, Network Input, HTTP Event Collector
EXPOSE 8000/tcp \
       8089/tcp \
       8191/tcp \
       9997/tcp \
       1514 \
       8088/tcp

# add splunk:splunk user
RUN groupadd -r ${SPLUNK_GROUP} \
    && useradd -r -m -g ${SPLUNK_GROUP} ${SPLUNK_USER}

# make the "en_US.UTF-8" locale so splunk will be utf-8 enabled by default
RUN apt-get update && \
    apt-get install -y locales && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

RUN rm -rf /etc/service/sshd /etc/my_init.d/00_regen_ssh_host_keys.sh

# install very base dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      bzip2 \
      ca-certificates \
      curl \
      git \
      libgssapi-krb5-2 \
      procps \
      pstack \
      python-software-properties \
      software-properties-common \
      sudo \
      unzip \
      wget \
      xz-utils && \
    apt-get --purge remove openjdk* && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/*

# Download official Splunk release, verify checksum and unzip in /opt/splunk
# Also backup etc folder, so it will be later copied to the linked volume
RUN \
  wget -qO /tmp/${SPLUNK_FILENAME} \
    https://download.splunk.com/products/${SPLUNK_PRODUCT}/releases/${SPLUNK_VERSION}/linux/${SPLUNK_FILENAME} && \
  wget -qO /tmp/${SPLUNK_FILENAME}.md5 \
    https://download.splunk.com/products/${SPLUNK_PRODUCT}/releases/${SPLUNK_VERSION}/linux/${SPLUNK_FILENAME}.md5 && \
  (cd /tmp && md5sum -c ${SPLUNK_FILENAME}.md5) && \
  tar xzf /tmp/${SPLUNK_FILENAME} --strip 1 -C ${SPLUNK_HOME} && \
  rm /tmp/${SPLUNK_FILENAME} && \
  rm /tmp/${SPLUNK_FILENAME}.md5 && \
  # Accept the splunk license on first run \
  ./bin/splunk version --accept-license

# Create HEC input
RUN mkdir -p ./etc/apps/splunk_httpinput/local
COPY ./splunk/inputs.conf ./etc/apps/splunk_httpinput/local/inputs.conf

# Allow remote logging and reduce the minFreeSpace size to 1GB
RUN mkdir -p ./etc/system/local
COPY ./splunk/server.conf /opt/splunk/etc/system/local/server.conf

HEALTHCHECK --interval=10s --timeout=60s --start-period=20s --retries=10 \
  CMD curl -ksSL "https://localhost:8088/services/collector/health" || exit 1

ENTRYPOINT ["./bin/splunk"]
CMD ["start", "--nodaemon"]
