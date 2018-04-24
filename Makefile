PLUGIN_NAME=splunk/docker-logging-plugin
PLUGIN_TAG=2.0.0
PLUGIN_DIR=./splunk-logging-plugin

all: clean docker rootfs create
package: clean docker rootfs zip

clean:
	@echo "### rm ${PLUGIN_DIR}"
	rm -rf ${PLUGIN_DIR}

docker:
	@echo "### docker build: rootfs image with splunk-logging-plugin"
	docker build -t ${PLUGIN_NAME}:rootfs .

rootfs:
	@echo "### create rootfs directory in ${PLUGIN_DIR}/rootfs"
	mkdir -p ${PLUGIN_DIR}/rootfs
	docker create --name tmprootfs ${PLUGIN_NAME}:rootfs
	docker export tmprootfs | tar -x -C ${PLUGIN_DIR}/rootfs
	@echo "### copy config.json to ${PLUGIN_DIR}/"
	cp config.json ${PLUGIN_DIR}/
	docker rm -vf tmprootfs

create:
	@echo "### remove existing plugin ${PLUGIN_NAME}:${PLUGIN_TAG} if exists"
	docker plugin rm -f ${PLUGIN_NAME}:${PLUGIN_TAG} || true
	@echo "### create new plugin ${PLUGIN_NAME}:${PLUGIN_TAG} from ${PLUGIN_DIR}"
	docker plugin create ${PLUGIN_NAME}:${PLUGIN_TAG} ${PLUGIN_DIR}

zip:
	@echo "### create a tar.gz for plugin"
	tar -cvzf splunk-logging-plugin.tar.gz ${PLUGIN_DIR}

enable:
	@echo "### enable plugin ${PLUGIN_NAME}:${PLUGIN_TAG}"
	docker plugin enable ${PLUGIN_NAME}:${PLUGIN_TAG}

push: clean docker rootfs create enable
	@echo "### push plugin ${PLUGIN_NAME}:${PLUGIN_TAG}"
	docker plugin push ${PLUGIN_NAME}:${PLUGIN_TAG}
