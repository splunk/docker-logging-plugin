import pytest
import time
import uuid
import os
import math
import logging
from ..common import request_start_logging,  \
    check_events_from_splunk, request_stop_logging, \
    start_log_producer_interval, start_logging_plugin


@pytest.mark.parametrize("test_input", [
    8,
    3,
])
def test_post_messages_frequency(setup, test_input):
    '''
    Test that user can change the http event post frequency
    with enviornment variable.

    This test writes two events per specified interval. The
    two events should be sent to splunk in the same batches.


    Then compare the _indextime of the two batches in splunk. The
    difference of the two _indextime should roughly match the
    specified interval
    '''
    os.environ["SPLUNK_LOGGING_DRIVER_POST_MESSAGES_FREQUENCY"] \
        = str(test_input) + "s"

    start_logging_plugin(setup["plugin_path"])
    time.sleep(2)

    logging.getLogger().info("testing test_post_messages_frequency")
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]

    # produce events at the specified frequency for a duration
    # of 2 * interval. This will produce 2 events per interval
    start_log_producer_interval(file_path,
                                u_id,
                                interval=test_input / 2,
                                duration=test_input * 2)

    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"])

    # sleep enough time for plugin to read all the messages
    # produced within the duraion
    time.sleep(test_input * 2 + 1)

    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-1m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)

    assert len(events) > 2

    time1 = events[0]["_indextime"]
    time2 = events[2]["_indextime"]

    # check that the two events' index time has about the specified interval
    # note that this is an estimate as it is affected by the latency
    assert int(time1) - int(time2) == test_input


@pytest.mark.parametrize("test_input", [
    50,
])
def test_batch_size(setup, test_input):
    '''
    Test that user can change the event batch size.

    This test writes at least 2 times of the specified batch size events to the
    pipe. The plugin batches the events to send to Splunk and Splunk indexes
    each batch with same _indextime. So for each _indextime, there should have
    number of events that roughly the same as the batch size.
    '''
    os.environ["SPLUNK_LOGGING_DRIVER_POST_MESSAGES_BATCH_SIZE"] \
        = str(test_input)

    start_logging_plugin(setup["plugin_path"])
    time.sleep(2)

    logging.getLogger().info("testing test_batch_size")
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]

    # produce events at the specified frequency for a duration
    # of 2 * frequency. This will produce
    duration = test_input * 0.1 * 3
    start_log_producer_interval(file_path,
                                u_id,
                                interval=0.1,
                                duration=duration)

    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"])

    # sleep enough time for plugin to read all the messages
    # produced within the duraion
    time.sleep(duration)

    request_stop_logging(file_path)

    time.sleep(5)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-2m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)

    assert len(events) > test_input

    res = {}
    # count events per _indextime
    for event in events:
        if not event["_indextime"] in res:
            res[event["_indextime"]] = 1
        else:
            res[event["_indextime"]] += 1

    count = 0
    # for each _indextime, there should be about the same number of
    # specified batch size
    for key, val in res.items():
        if math.fabs(val - test_input) < 3:
            count = count + 1

    assert count >= 2
