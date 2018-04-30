import json
import uuid
from urlparse import urljoin

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class HECError(Exception):
    def __init__(self, response):
        self._response = response

    def __str__(self):
        return self._response.content

    @property
    def status_code(self):
        return self._response.status_code


class HECWriter(object):

    def __init__(self, hec_url, hec_token):
        self._uri = urljoin(hec_url, '/services/collector')
        self._headers = {
            'Authorization': 'Splunk {}'.format(hec_token),
            'User-Agent': 'curl/7.29.0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
        }
        self._session = requests.Session()

    def write(self, events):
        '''
        @events: list of dict object
        {
            'index': <index>,
            'source': <source>,
            'sourcetype': <sourcetype>,
            'host': <host>,
            'event': <data>,
        }
        '''

        data = '\n'.join(json.dumps(event) for event in events)

        response = self._session.post(
            self._uri, data=data, headers=self._headers, verify=False)
        if response.status_code != 200:
            raise HECError(response)


class RawHECWriter(object):

    def __init__(self, hec_url, hec_token, channel=None):
        if not channel:
            self._channel = str(uuid.uuid4())
        else:
            self._channel = channel

        self._uri = urljoin(hec_url, '/services/collector/raw')
        self._headers = {
            'Authorization': 'Splunk {}'.format(hec_token),
            'User-Agent': 'curl/7.29.0',
            'Connection': 'keep-alive',
            'x-splunk-request-channel': '{}'.format(self._channel),
        }
        self._session = requests.Session()

    def write(self, events):
        '''
        @event: list of dict object
        {
            'index': <index>,
            'source': <source>,
            'sourcetype': <sourcetype>,
            'host': <host>,
            'event': <data>,
        }
        '''

        for event in events:
            data = event['event']
            meta = event
            del meta['event']

            response = self._session.post(
                self._uri, data=data, params=meta,
                headers=self._headers, verify=False)
            if response.status_code != 200:
                raise HECError(response)


if __name__ == '__main__':
    hec_url = 'https://10.16.29.64:8088'
    hec_token = '1CB57F19-DC23-419A-8EDA-BA545DD3674D'
    writer = HECWriter(hec_url, hec_token)
    events = [
        {
            'sourcetype': 'kchen',
            'source': 'kchen',
            'host': 'kchen',
            'index': 'main',
            'event': '{"key": "i love you"}',
        }
    ]
    writer.write(events)

    raw_writer = RawHECWriter(hec_url, hec_token)
    raw_writer.write(events)