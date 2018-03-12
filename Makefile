PLUGIN_NAME=splunk-log-plugin
PLUGIN_TAG=latest

all: clean docker rootfs create test

clean:
	@echo "### rm ./plugin"
	rm -rf ./plugin

docker:
	@echo "### docker build: rootfs image with splunk-log-plugin"
	docker build -t ${PLUGIN_NAME}:rootfs .

rootfs:
	@echo "### create rootfs directory in ./plugin/rootfs"
	mkdir -p ./plugin/rootfs
	docker create --name tmprootfs ${PLUGIN_NAME}:rootfs
	docker export tmprootfs | tar -x -C ./plugin/rootfs
	@echo "### copy config.json to ./plugin/"
	cp config.json ./plugin/
	docker rm -vf tmprootfs

create:
	@echo "### remove existing plugin ${PLUGIN_NAME}:${PLUGIN_TAG} if exists"
	docker plugin rm -f ${PLUGIN_NAME}:${PLUGIN_TAG} || true
	@echo "### create new plugin ${PLUGIN_NAME}:${PLUGIN_TAG} from ./plugin"
	docker plugin create ${PLUGIN_NAME}:${PLUGIN_TAG} ./plugin

enable:
	@echo "### enable plugin ${PLUGIN_NAME}:${PLUGIN_TAG}"
	docker plugin enable ${PLUGIN_NAME}:${PLUGIN_TAG}

push: clean docker rootfs create enable
	@echo "### push plugin ${PLUGIN_NAME}:${PLUGIN_TAG}"
	docker plugin push ${PLUGIN_NAME}:${PLUGIN_TAG}

test:
	@go test