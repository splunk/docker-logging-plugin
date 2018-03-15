import pytest
import time
import uuid
import logging
from ..common import request_start_logging,  \
    check_events_from_splunk, request_stop_logging, \
    start_log_producer_from_input


@pytest.mark.parametrize("test_input,expected", [
    (None, 1),
    ("history", 1)
])
def test_splunk_index(setup, test_input, expected):
    '''
    Test that user specified index can successfully index the
    log stream from docker. If no index is specified, default
    index "main" will be used.

    Note that the HEC token on splunk side needs to be configured
    to accept the specified index.
    '''
    logging.getLogger().info("testing test_splunk_index input={0} \
                expected={1} event(s)".format(test_input, expected))
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    start_log_producer_from_input(file_path, [("test index", False)], u_id)

    index = test_input if test_input else "main"
    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"],
                          options={"splunk-index": index})

    # wait for 10 seconds to allow messages to be sent
    time.sleep(10)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(index=index,
                                      id=u_id,
                                      start_time="-1m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected


@pytest.mark.parametrize("test_input,expected", [
    (None, 1),
    ("test_source", 1)
])
def test_splunk_source(setup, test_input, expected):
    '''
    Test that docker logs can be indexed with the specified
    source successfully. If no source is specified, the default
    "http:docker" is used
    '''

    logging.getLogger().info("testing test_splunk_source input={0} \
                expected={1} event(s)".format(test_input, expected))
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    start_log_producer_from_input(file_path, [("test source", False)], u_id)

    options = {}
    if test_input:
        options = {"splunk-source": test_input}

    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"],
                          options=options)

    source = test_input if test_input else "http:docker"
    # wait for 10 seconds to allow messages to be sent
    time.sleep(10)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id="source={0} {1}".format(source, u_id),
                                      start_time="-2m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected


@pytest.mark.parametrize("test_input,expected", [
    (None, 1),
    ("test_source_type", 1)
])
def test_splunk_source_type(setup, test_input, expected):
    '''
    Test that docker logs can be indexed with the specified
    sourcetype successfully. If no source is specified, the default
    "httpevent" is used
    '''

    logging.getLogger().info("testing test_splunk_source_type input={0} \
                expected={1} event(s)".format(test_input, expected))
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    start_log_producer_from_input(file_path, [("test source", False)], u_id)

    options = {}
    if test_input:
        options = {"splunk-sourcetype": test_input}
    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"],
                          options=options)

    sourcetype = test_input if test_input else "httpevent"

    # wait for 10 seconds to allow messages to be sent
    time.sleep(10)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id="sourcetype={0} {1}"
                                         .format(sourcetype, u_id),
                                      start_time="-2m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected
