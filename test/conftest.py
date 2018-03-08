import pytest
import time
from common import start_logging_plugin, \
    kill_logging_plugin

plugin_process = "/home/ec2-user/plugin/splunk-log-plugin"

@pytest.fixture
def setup(request):
    kill_logging_plugin(plugin_process)
    start_logging_plugin(plugin_process)
    time.sleep(2)
    request.addfinalizer(teardown_method)

    return request

def teardown_method():
    kill_logging_plugin(plugin_process)