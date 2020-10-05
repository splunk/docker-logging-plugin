import pytest
import time
import uuid
import os
import logging
import json
import socket
from urllib.parse import urlparse
from ..common import request_start_logging,  \
    check_events_from_splunk, request_stop_logging, \
    start_log_producer_from_input


@pytest.mark.parametrize("test_input,expected", [
    (None, 1)
])

def test_splunk_index_1(setup, test_input, expected):
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
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(index=index,
                                      id=u_id,
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected

@pytest.mark.parametrize("test_input,expected", [
     ("history", 1)
])

def test_splunk_index_2(setup, test_input, expected):
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
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(index=index,
                                      id=u_id,
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected



@pytest.mark.parametrize("test_input,expected", [
    (None, 1),
])
def test_splunk_source_1(setup, test_input, expected):
    '''
    Test that docker logs can be indexed with the specified
    source successfully. If no source is specified, the default
    source from docker is used
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

    source = test_input if test_input else "*"
    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id="source={0} {1}".format(source, u_id),
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected

@pytest.mark.parametrize("test_input,expected", [
    ("test_source", 1)
])
def test_splunk_source_2(setup, test_input, expected):
    '''
    Test that docker logs can be indexed with the specified
    source successfully. If no source is specified, the default
    source from docker is used
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

    source = test_input if test_input else "*"
    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id="source={0} {1}".format(source, u_id),
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected



@pytest.mark.parametrize("test_input,expected", [
    (None, 1),
])
def test_splunk_source_type_1(setup, test_input, expected):
    '''
    Test that docker logs can be indexed with the specified
    sourcetype successfully. If no source is specified, the default
    "splunk_connect_docker" is used
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

    sourcetype = test_input if test_input else "splunk_connect_docker"

    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id="sourcetype={0} {1}"
                                         .format(sourcetype, u_id),
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected

@pytest.mark.parametrize("test_input,expected", [
    ("test_source_type", 1)
])
def test_splunk_source_type_2(setup, test_input, expected):
    '''
    Test that docker logs can be indexed with the specified
    sourcetype successfully. If no source is specified, the default
    "splunk_connect_docker" is used
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

    sourcetype = test_input if test_input else "splunk_connect_docker"

    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id="sourcetype={0} {1}"
                                         .format(sourcetype, u_id),
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected


def test_splunk_ca(setup):
    '''
    Test that docker logging plugin can use the server certificate to
    verify the server identity

    The server cert used here is the default CA shipping in splunk
    '''
    logging.getLogger().info("testing test_splunk_ca")
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    start_log_producer_from_input(file_path, [("test ca", False)], u_id)
    current_dir = os.path.dirname(os.path.realpath(__file__))

    options = {
        "splunk-insecureskipverify": "false",
        "splunk-capath": current_dir + "/cacert.pem",
        "splunk-caname": "SplunkServerDefaultCert"
    }

    parsed_url = urlparse(setup["splunk_hec_url"])
    hec_ip = parsed_url.hostname
    hec_port = parsed_url.port

    # check if it is an IP address
    try:
        socket.inet_aton(hec_ip)
    except socket.error:
        # if it is not an IP address, it is a hostname
        # do a hostname to IP lookup
        hec_ip = socket.gethostbyname(hec_ip)

    splunk_hec_url = "https://SplunkServerDefaultCert:{0}".format(hec_port)

    if "SplunkServerDefaultCert" not in open('/etc/hosts').read():
        file = open("/etc/hosts", "a")
        file.write("{0}\tSplunkServerDefaultCert".format(hec_ip))
        file.close()

    request_start_logging(file_path,
                          splunk_hec_url,
                          setup["splunk_hec_token"],
                          options=options)

    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == 1


@pytest.mark.parametrize("test_input,expected", [
    ("json", 1),
])
def test_splunk_format_json(setup, test_input, expected):
    '''
    Test that different splunk format: json, raw, inline can be handled
    correctly.

    json: tries to parse the given message in to a json object and send both
          source and log message to splunk
    inline: treats the given message as a string and wrap it in a json object
            with source and send the json string to splunk
    raw: sends the raw message to splunk
    '''
    logging.getLogger().info("testing test_splunk_format input={0} \
                expected={1} event(s)".format(test_input, expected))
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    test_string = '{"test": true, "id": "' + u_id + '"}'
    start_log_producer_from_input(file_path, [(test_string, False)], u_id)

    options = {}
    if test_input:
        options = {"splunk-format": test_input}

    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"],
                          options=options)

    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected

    event = events[0]["_raw"]
    if test_input == "json" or test_input == "inline":
        try:
            parsed_event = json.loads(event)
        except Exception:
            pytest.fail("{0} can't be parsed to json"
                        .format(event))
            if test_input == "json":
                assert parsed_event["line"] == json.loads(test_string)
            elif test_input == "inline":
                assert parsed_event["line"] == test_string
    elif test_input == "raw":
        assert event == test_string

@pytest.mark.parametrize("test_input,expected", [
    ("inline", 1),
])
def test_splunk_format_inline(setup, test_input, expected):
    '''
    Test that different splunk format: json, raw, inline can be handled
    correctly.

    json: tries to parse the given message in to a json object and send both
          source and log message to splunk
    inline: treats the given message as a string and wrap it in a json object
            with source and send the json string to splunk
    raw: sends the raw message to splunk
    '''
    logging.getLogger().info("testing test_splunk_format input={0} \
                expected={1} event(s)".format(test_input, expected))
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    test_string = '{"test": true, "id": "' + u_id + '"}'
    start_log_producer_from_input(file_path, [(test_string, False)], u_id)

    options = {}
    if test_input:
        options = {"splunk-format": test_input}

    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"],
                          options=options)

    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected

    event = events[0]["_raw"]
    if test_input == "json" or test_input == "inline":
        try:
            parsed_event = json.loads(event)
        except Exception:
            pytest.fail("{0} can't be parsed to json"
                        .format(event))
            if test_input == "json":
                assert parsed_event["line"] == json.loads(test_string)
            elif test_input == "inline":
                assert parsed_event["line"] == test_string
    elif test_input == "raw":
        assert event == test_string

@pytest.mark.parametrize("test_input,expected", [
    ("raw", 1)
])
def test_splunk_format_raw(setup, test_input, expected):
    '''
    Test that different splunk format: json, raw, inline can be handled
    correctly.

    json: tries to parse the given message in to a json object and send both
          source and log message to splunk
    inline: treats the given message as a string and wrap it in a json object
            with source and send the json string to splunk
    raw: sends the raw message to splunk
    '''
    logging.getLogger().info("testing test_splunk_format input={0} \
                expected={1} event(s)".format(test_input, expected))
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    test_string = '{"test": true, "id": "' + u_id + '"}'
    start_log_producer_from_input(file_path, [(test_string, False)], u_id)

    options = {}
    if test_input:
        options = {"splunk-format": test_input}

    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"],
                          options=options)

    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == expected

    event = events[0]["_raw"]
    if test_input == "json" or test_input == "inline":
        try:
            parsed_event = json.loads(event)
        except Exception:
            pytest.fail("{0} can't be parsed to json"
                        .format(event))
            if test_input == "json":
                assert parsed_event["line"] == json.loads(test_string)
            elif test_input == "inline":
                assert parsed_event["line"] == test_string
    elif test_input == "raw":
        assert event == test_string


@pytest.mark.parametrize("test_input, has_exception", [
    ("true", True),
])
def test_splunk_verify_connection(setup, test_input, has_exception):
    '''
    Test that splunk-verify-connection option works as expected.

    In this test, given a wrong splunk hec endpoint/token:
    - if splunk-verify-connection == false, the plugin will
      NOT throw any exception at the start up
    - if splunk-verify-connection == true, the plugin will
      error out at the start up
    '''
    logging.getLogger().info("testing splunk_verify_connection")
    file_path = setup["fifo_path"]
    u_id = str(uuid.uuid4())
    start_log_producer_from_input(file_path, [("test verify", False)], u_id)
    options = {"splunk-verify-connection": test_input}
    try:
        request_start_logging(file_path,
                              "https://localhost:8088",
                              "00000-00000-0000-00000",  # this should fail
                              options=options)

        assert not has_exception
    except Exception as ex:
        assert has_exception


@pytest.mark.parametrize("test_input, has_exception", [
    ("-1", True),
    ("0", False),
    ("5", False),
    ("9", False),
    ("10", True)
])
def test_splunk_gzip(setup, test_input, has_exception):
    '''
    Test that the http events can be send to splunk with gzip enabled.

    Acceptable gzip levels are from 0 - 9. Gzip level out of the range
    will thrown an exception.
    '''
    logging.getLogger().info("testing test_splunk_gzip")
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    start_log_producer_from_input(file_path, [("test gzip", False)], u_id)

    options = {"splunk-gzip": "true", "splunk-gzip-level": test_input}

    try:
        request_start_logging(file_path,
                              setup["splunk_hec_url"],
                              setup["splunk_hec_token"],
                              options=options)
    except Exception as ex:
        assert has_exception

    if not has_exception:
        # wait for 10 seconds to allow messages to be sent
        time.sleep(15)
        request_stop_logging(file_path)

        # check that events get to splunk
        events = check_events_from_splunk(id=u_id,
                                          start_time="-15m@m",
                                          url=setup["splunkd_url"],
                                          user=setup["splunk_user"],
                                          password=setup["splunk_password"])
        logging.getLogger().info("Splunk received %s events in the last " +
                                 "minute with u_id=%s",
                                 len(events), u_id)
        assert len(events) == 1


def test_splunk_tag(setup):
    '''
    Test the users can add customized tag to the events and splunk
    preserves the tags added.
    '''
    logging.getLogger().info("testing test_splunk_tag")
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    start_log_producer_from_input(file_path, [("test tag", False)], u_id)

    options = {"tag": "test-tag"}
    request_start_logging(file_path,
                          setup["splunk_hec_url"],
                          setup["splunk_hec_token"],
                          options=options)

    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    # check that events get to splunk
    events = check_events_from_splunk(id=u_id,
                                      start_time="-15m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with u_id=%s",
                             len(events), u_id)
    assert len(events) == 1
    parsed_event = json.loads(events[0]["_raw"])
    assert parsed_event["tag"] == options["tag"]


def test_splunk_telemety(setup):
    '''
    Test that telemetry event is sent to _introspection index.
    '''
    logging.getLogger().info("testing telemetry")
    u_id = str(uuid.uuid4())

    file_path = setup["fifo_path"]
    start_log_producer_from_input(file_path, [("test telemetry", False)], u_id)

    options = {"splunk-sourcetype": "telemetry"}

    request_start_logging(file_path,
                              setup["splunk_hec_url"],
                              setup["splunk_hec_token"],
                              options=options)

    # wait for 10 seconds to allow messages to be sent
    time.sleep(15)
    request_stop_logging(file_path)

    index = "_introspection"
    sourcetype = "telemetry"


    # check that events get to splunk
    events = check_events_from_splunk(index=index,
                                      id="data.sourcetype={0}".format(sourcetype),
                                      start_time="-5m@m",
                                      url=setup["splunkd_url"],
                                      user=setup["splunk_user"],
                                      password=setup["splunk_password"])
    logging.getLogger().info("Splunk received %s events in the last minute" +
                             " with component=app.connect.docker",
                             len(events))
    assert len(events) == 1
