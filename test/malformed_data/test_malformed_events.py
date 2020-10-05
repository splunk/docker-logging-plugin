"""
Copyright 2018 Splunk, Inc..

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pytest
import time
import uuid
import logging
from ..common import request_start_logging,  \
    check_events_from_splunk, request_stop_logging, \
    start_log_producer_from_input


@pytest.mark.parametrize("test_input,expected", [
    ([("", False)], 0)  # should not be sent to splunk
])
def test_malformed_empty_string_1(setup, test_input, expected):
    '''
    Test that the logging plugin can handle various type of input correctly.
    Expected behavior is that:
        * Empty string or string with only spaces should be neglected
        * Non empty strings should be sent to Splunk
        * Non UTF-8 decodable string should still be sent to Splunk
    '''
    logging.getLogger().info("testing test_malformed_empty_string input={0} \
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
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute " +
                             "with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected

@pytest.mark.parametrize("test_input,expected", [
    ([(" ", False)], 0)  # should not be sent to splunk
])
def test_malformed_empty_string_2(setup, test_input, expected):
    '''
    Test that the logging plugin can handle various type of input correctly.
    Expected behavior is that:
        * Empty string or string with only spaces should be neglected
        * Non empty strings should be sent to Splunk
        * Non UTF-8 decodable string should still be sent to Splunk
    '''
    logging.getLogger().info("testing test_malformed_empty_string input={0} \
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
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute " +
                             "with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected

@pytest.mark.parametrize("test_input,expected", [
    ([("\xF0\xA4\xAD", False)] 1),  # non utf-8 decodable chars
                                     # should make it to splunk
                                             # be sent to splunk
])

def test_malformed_empty_string_3(setup, test_input, expected):
    '''
    Test that the logging plugin can handle various type of input correctly.
    Expected behavior is that:
        * Empty string or string with only spaces should be neglected
        * Non empty strings should be sent to Splunk
        * Non UTF-8 decodable string should still be sent to Splunk
    '''
    logging.getLogger().info("testing test_malformed_empty_string input={0} \
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
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute " +
                             "with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected

@pytest.mark.parametrize("test_input,expected", [
    ([("hello", False)], 1)  # normal string should always to sent to splunk
])

def test_malformed_empty_string_4(setup, test_input, expected):
    '''
    Test that the logging plugin can handle various type of input correctly.
    Expected behavior is that:
        * Empty string or string with only spaces should be neglected
        * Non empty strings should be sent to Splunk
        * Non UTF-8 decodable string should still be sent to Splunk
    '''
    logging.getLogger().info("testing test_malformed_empty_string input={0} \
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
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute " +
                             "with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected
@pytest.mark.parametrize("test_input,expected", [
    ([("{'test': 'incomplete}", False)], 1)  # malformed json string should
                                             # be sent to splunk
])

def test_malformed_empty_string_5(setup, test_input, expected):
    '''
    Test that the logging plugin can handle various type of input correctly.
    Expected behavior is that:
        * Empty string or string with only spaces should be neglected
        * Non empty strings should be sent to Splunk
        * Non UTF-8 decodable string should still be sent to Splunk
    '''
    logging.getLogger().info("testing test_malformed_empty_string input={0} \
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
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute " +
                             "with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected
