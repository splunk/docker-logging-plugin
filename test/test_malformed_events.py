import pytest
import time
import uuid
from common import start_logging_plugin, open_fifo,\
    write_proto_buf_message, request_start_logging, \
    check_events_from_splunk, request_stop_logging, \
    kill_logging_plugin

plugin_process = "/home/ec2-user/plugin/splunk-log-plugin"
class TestClass:
    def setup_method(self, method):
        kill_logging_plugin(plugin_process)
        start_logging_plugin(plugin_process)
        time.sleep(2)
 
    def teardown_method(self, method):
        kill_logging_plugin(plugin_process)

    @pytest.mark.parametrize("test_input,expected", [
        ("", 0),
        (" ", 0),
        ("hello", 1),
    ])
    def test_malformed_empty_string(self, test_input, expected):
        id = str(uuid.uuid4())
        
        file = "./pipe"
        f = open_fifo(file)
        write_proto_buf_message(f, message=test_input, id=id)
        request_start_logging(file)

        # wait for 10 seconds to allow messages to be sent
        time.sleep(10)
        request_stop_logging(file)

        events = check_events_from_splunk(id=id, start_time="-1m@m")
        assert len(events) == expected
        