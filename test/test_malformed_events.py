import pytest
import time
import uuid
from common import start_logging_plugin, open_fifo,\
    write_proto_buf_message, request_start_logging, \
    check_events_from_splunk, request_stop_logging, \
    kill_logging_plugin



@pytest.mark.parametrize("test_input,expected", [
    ("", 0),
    (" ", 0),
    ("hello", 1),
])
def test_malformed_empty_string(setup, test_input, expected):
    id = str(uuid.uuid4())
    
    file = "/home/ec2-user/pipe"
    f = open_fifo(file)
    write_proto_buf_message(f, message=test_input, source=id)
    request_start_logging(file)

    # wait for 10 seconds to allow messages to be sent
    time.sleep(10)
    request_stop_logging(file)

    events = check_events_from_splunk(id=id, start_time="-1m@m")
    assert len(events) == expected
