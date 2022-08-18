PARTIAL_TESTS = test_partial_log_1 test_partial_log_2 test_partial_log_flush_timeout_1 test_partial_log_flush_timeout_2 test_partial_log_flush_size_limit
CONFIG_TESTS = test_splunk_index_1 test_splunk_index_2 test_splunk_source_1 test_splunk_source_2 test_splunk_source_type_1 test_splunk_source_type_2 test_splunk_ca test_splunk_format_json test_splunk_format_inline test_splunk_format_raw test_splunk_verify_connection test_splunk_gzip_1 test_splunk_gzip_2 test_splunk_gzip_3 test_splunk_gzip_4 test_splunk_gzip_5 test_splunk_tag
MALFORMED_TESTS = test_malformed_empty_string_1 test_malformed_empty_string_2 test_malformed_empty_string_3 test_malformed_empty_string_4 test_malformed_empty_string_5

.PHONY: setup-venv setup-splunk test-partial test-config test-malformed

setup-venv:
	if [ ! -d venv/ ] ; then python3.8 -m venv venv ; fi
	. venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

setup-splunk:
	docker compose up -d
	./wait-for-splunk.sh

test-partial:
	$(foreach var,$(PARTIAL_TESTS),sudo venv/bin/python -m pytest --cache-clear \
	--splunkd-url https://localhost:8089 \
	--splunk-user admin \
	--splunk-password notchangeme \
	--splunk-hec-url https://localhost:8088 \
	--splunk-hec-token abcd1234 \
	--docker-plugin-path ../splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /tmp/pipe \
	-p no:warnings partial_log/test_partial_log.py::$(var) || exit;)

test-config:
	$(foreach var,$(CONFIG_TESTS),sudo venv/bin/python -m pytest --cache-clear \
	--splunkd-url https://localhost:8089 \
	--splunk-user admin \
	--splunk-password notchangeme \
	--splunk-hec-url https://localhost:8088 \
	--splunk-hec-token abcd1234 \
	--docker-plugin-path ../splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /tmp/pipe \
	-p no:warnings config_params/test_cofig_params.py::$(var) || exit;)

test-malformed:
	$(foreach var,$(MALFORMED_TESTS),sudo venv/bin/python -m pytest --cache-clear \
	--splunkd-url https://localhost:8089 \
	--splunk-user admin \
	--splunk-password notchangeme \
	--splunk-hec-url https://localhost:8088 \
	--splunk-hec-token abcd1234 \
	--docker-plugin-path ../splunk-logging-plugin/rootfs/bin/splunk-logging-plugin \
	--fifo-path /tmp/pipe \
	-p no:warnings malformed_data/test_malformed_events.py::$(var) || exit;)
