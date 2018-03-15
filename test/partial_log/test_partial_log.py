import pytest
import time
import uuid
import os
import logging
from ..common import request_start_logging,  \
    check_events_from_splunk, request_stop_logging, \
    start_log_producer_from_input, start_log_producer_from_file


@pytest.mark.parametrize("test_input, expected", [
    ([("start", True), ("in the middle", True), ("end", False)], 1),
    ([("start2", False), ("new start", True), ("end2", False)], 2)
])
def test_partial_log(setup, test_input, expected):
    '''
    Test that the logging plugin can handle partial logs correctly.
    Expected behavior is that the plugin keeps appending the message
    hen partial flag is True and stop and flush when it reaches False
    '''
    logging.getLogger().info("testing test_partial_log input={0} \
                expected={1} event(s)".format(test_input, expected))
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    start_log_producer_from_input(file_path, test_input, u_id)
    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"])

    # wait for 10 seconds to allow messages to be sent
    time.sleep(10)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-5m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in \
                             the last minute with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected


@pytest.mark.parametrize("test_input, expected", [
   ([("start", True), ("mid", True), ("end", False)], 3),
   ([("start2", True), ("new start", True), ("end2", True)], 3)
])
def test_partial_log_flush_timeout(setup, test_input, expected):
    '''
    Test that the logging plugin can flush the buffer for partial
    log. If the next partial message didn't arrive in expected
    time (default 1 sec), it should flush the buffer anyway
    '''
    logging.getLogger().info("testing test_partial_log_flush_timeout input={0} \
                expected={1} event(s)".format(test_input, expected))
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]

    start_log_producer_from_input(file_path, test_input, u_id, 1)
    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"])

    # wait for 15 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-5m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute " +
                             "with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected


def test_partial_log_flush_size_limit(setup):
    '''
    Test that the logging plugin can flush the buffer when it reaches
    the buffer size limit (1mb)
    '''
    logging.getLogger().info("testing test_partial_log_flush_size_limit")
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                    os.path.dirname(__file__)))
    test_file_path = os.path.join(__location__, "test_file.txt")

    start_log_producer_from_file(file_path, u_id, test_file_path)

    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"])

    # wait for 15 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-5m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute "
                             "with u_id=%s",
                             len(events), u_id)

    assert len(events) == 2
