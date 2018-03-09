import pytest
import time
import uuid
from common import start_logging_plugin, open_fifo,\
    write_proto_buf_message, request_start_logging, \
    check_events_from_splunk, request_stop_logging, \
    kill_logging_plugin



@pytest.mark.parametrize("test_input,expected", [
    ("", 0), # should not be sent to splunk
    (" ", 0), # should not be sent to splunk
    ("\xF0\xA4\xAD", 1), # non utf-8 decodable chars should still make it to splunk
    ("hello", 1), # normal string should always to sent to splunk
])
def test_malformed_empty_string(setup, test_input, expected):
    id = str(uuid.uuid4())

    file = setup["fifo_path"]
    f = open_fifo(file)
    write_proto_buf_message(f, message=test_input, source=id)
    request_start_logging(file)

    # wait for 10 seconds to allow messages to be sent
    time.sleep(10)
    request_stop_logging(file)

    # check that events get to splunk
    events = check_events_from_splunk(id=id, start_time="-1m@m", url=setup["splunkd_url"],
                                      user=setup["splunk_user"], password=setup["splunk_password"])
    assert len(events) == expected
