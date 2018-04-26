#!/usr/bin/python

import os
import time
import logging
import requests

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except:
    pass

logging.basicConfig(
    format='%(asctime)-15s mod=%(module)s func=%(funcName)s line=%(lineno)d %(message)s',
    level=logging.INFO)

DEFAULT_ADMIN = 'admin'
DEFAULT_PASSWORD = 'changeme'


class HecTokenManager(object):
    def __init__(self, token, token_name, source_type):
        self.token = token
        self.token_name = token_name
        self.source_type = source_type

    def create_hec_tokens(self, indexers):

        for indexer in indexers:
            #self.create_token_with_ack(indexer)
            #logging.info('token created for indexer:  %s', indexer)
            self.enable_ack_idle_cleanup(indexer)
            logging.info('AckIdleCleanup enabled for indexer:  %s', indexer)

    def create_token_with_ack(self, host_name):
        data = {
            'name': self.token_name,
            'token': self.token,
            'index': 'main',
            'indexes': 'main',
            'useACK': '1',
            'disabled': '0',
            'sourcetype': self.source_type
        }

        uri = 'https://{}:8089/servicesNS/nobody/splunk_httpinput/data/inputs/http?output_mode=json'.format(host_name)

        auth = requests.auth.HTTPBasicAuth(DEFAULT_ADMIN, DEFAULT_PASSWORD)
        logging.info('posting to %s', uri)
        while 1:
            try:
                resp = requests.post(uri, data=data, auth=auth, verify=False)
            except Exception:
                logging.exception('failed to post to %s', uri)
                time.sleep(2)
            else:
                if resp.ok:
                    return

                if resp.status_code == 409:
                    # already exists
                    return

                logging.error('failed to post to %s, error=%s', uri, resp.text)
                time.sleep(2)

    def enable_ack_idle_cleanup(self, host_name):
        auth = requests.auth.HTTPBasicAuth(DEFAULT_ADMIN, DEFAULT_PASSWORD)
        data = {
            'ackIdleCleanup': 1
        }
        uri = 'https://{}:8089//services/data/inputs/http/http?output_mode=json'.format(host_name)
        logging.info('posting to %s', uri)
        try:
            resp = requests.post(uri, data=data, auth=auth, verify=False)
        except Exception:
            logging.exception('failed to post to %s', uri)
        else:
            if resp.ok:
                return

            else:
                logging.error('failed to post to %s, error=%s', uri, resp.text)
                raise


if __name__ == '__main__':
    indexers = ['10.141.65.148','10.141.70.165','10.141.65.52']
    mgt = HecTokenManager("", "test_name", "generic_singleline_notimestamp")