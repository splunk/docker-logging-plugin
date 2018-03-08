import json
import logging
import time
import LogEntry_pb2
import subprocess
import struct
import requests
import os
import requests_unixsocket
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)
timeout = 500
socket_start_url = "http+unix://%2Frun%2Fdocker%2Fplugins%2Fsplunklog.sock/LogDriver.StartLogging"
socket_stop_url = "http+unix://%2Frun%2Fdocker%2Fplugins%2Fsplunklog.sock/LogDriver.StopLogging"
splunk_user = "admin"
splunk_password = "notchangeme"

splunk_uri="https://52.53.254.149:8089"

def start_logging_plugin(plugin_path):
    args= (plugin_path)
    popen = subprocess.Popen(args, stdout=subprocess.PIPE)

    return popen

def kill_logging_plugin(plugin_path):
    os.system("killall " + plugin_path)

def read_file(file):
    f = open(file, 'r')

def open_fifo(fifo_location):
    fifo_writer = open(fifo_location, 'wb')

    return fifo_writer

def write_proto_buf_message(fifo_writer=None, source="test",
    time_nano = int(time.time() * 1000000000), message="",
    partial=False, id=""):
    log = LogEntry_pb2.LogEntry()
    log.source = id
    log.time_nano = time_nano
    log.line = bytes(message)
    log.partial = partial

    buf = log.SerializeToString(log)
    size = len(buf)

    size_buffer = bytearray(4)
    struct.pack_into(">i", size_buffer, 0, size)
    fifo_writer.write(size_buffer)
    fifo_writer.write(buf)

    fifo_writer.flush()
    fifo_writer.close()

def request_start_logging(file):
    reqObj = {
        "File": '/home/ec2-user/pipe',
        "Info": {
            "ContainerID": "test",
            "Config": {
                "splunk-url": "https://52.53.254.149:8088",
                "splunk-token": "7190F984-2C46-434F-8F3F-0455BD6B58A2",
                "splunk-insecureskipverify": "true",
                            "splunk-format": "json",
                            "tag": ""
            },
            "LogPath": "/home/ec2-user/test.txt"
        }
    }

    headers = {
        "Content-Type" : "application/json",
        "Host": "localhost"
    }


    session = requests_unixsocket.Session()
    res = session.post(
        socket_start_url,
        data=json.dumps(reqObj),
        headers=headers)
    
    if res.status_code != 200:
        raise Exception("Can't establish socket connection")

    logger.info(str(res))

def request_stop_logging(file):
    reqObj = {
        "File": file
    }
    session = requests_unixsocket.Session()
    res = session.post(
        socket_stop_url,
        data=json.dumps(reqObj)
    )

    if res.status_code != 200:
        raise Exception("Can't establish socket connection")

    logger.info(str(res))

def check_events_from_splunk(index="main", id=None, start_time="-24h@h", end_time="now"):
    query = _compose_search_query(index, id)
    events = _collect_events(query, start_time, end_time)

    return events

def _compose_search_query(index="main", id=None):
    return "search index={0} {1}".format(index, id)

def _collect_events(query, start_time, end_time):
    '''
    Collect events by running the given search query
    @param: query (search query)
    @param: start_time (search start time)
    @param: end_time (search end time)
    returns events
    '''

    url = '{0}/services/search/jobs?output_mode=json'.format(
        splunk_uri)
    logger.info('requesting: %s', url)
    data = {
        'search': query,
        'earliest_time': start_time,
        'latest_time': end_time,
    }

    create_job = _requests_retry_session().post(
        url,
        auth=(splunk_user, splunk_password),
        verify=False, data=data)
    _check_request_status(create_job)

    json_res = create_job.json()
    job_id = json_res['sid']
    events = _wait_for_job_and__get_events(job_id)

    return events

def _wait_for_job_and__get_events(job_id):
    '''
    Wait for the search job to finish and collect the result events
    @param: job_id
    returns events
    '''
    events = []
    job_url = '{0}/services/search/jobs/{1}?output_mode=json'.format(
        splunk_uri, str(job_id))
    logger.info('requesting: %s', job_url)

    for _ in range(timeout):
        res = _requests_retry_session().get(
            job_url,
            auth=(splunk_user, splunk_password),
            verify=False)
        _check_request_status(res)

        job_res = res.json()
        dispatch_state = job_res['entry'][0]['content']['dispatchState']

        if dispatch_state == 'DONE':
            events = _get_events(job_id)
            break
        if dispatch_state == 'FAILED':
            raise Exception('Search job: {0} failed'.format(job_url))
        time.sleep(1)

    return events

def _get_events(job_id):
    '''
    collect the result events from a search job
    @param: job_id
    returns events
    '''
    event_url = '{0}/services/search/jobs/{1}/events?output_mode=json'.format(
        splunk_uri, str(job_id))
    logger.info('requesting: %s', event_url)

    event_job = _requests_retry_session().get(
        event_url, auth=(splunk_user, splunk_password),
        verify=False)
    _check_request_status(event_job)

    event_job_json = event_job.json()
    events = event_job_json['results']

    return events


def _check_request_status(req_obj):
    '''
    check if a request is successful
    @param: req_obj
    returns True/False
    '''
    if not req_obj.ok:
        raise Exception('status code: {0} \n details: {1}'.format(
        str(req_obj.status_code), req_obj.text))

def _requests_retry_session(
        retries=10,
        backoff_factor=0.1,
        status_forcelist=(500, 502, 504)):
    '''
    create a retry session for HTTP/HTTPS requests
    @param: retries (num of retry time)
    @param: backoff_factor
    @param: status_forcelist (list of error status code to trigger retry)
    @param: session
    returns: session
    '''
    session = requests.Session()
    retry = Retry(
        total=int(retries),
        backoff_factor=backoff_factor,
        method_whitelist=frozenset(['GET', 'POST']),
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    return session
