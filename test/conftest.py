import pytest
import time
from common import start_logging_plugin, \
    kill_logging_plugin

# TODO: update the default to be more generic.
def pytest_addoption(parser):
    parser.addoption("--splunkd-url",
                     help="splunkd url used to send test data to. \
                          Eg: https://localhost:8089",
                     default="https://52.53.254.149:8089")
    parser.addoption("--splunk-user",
                     help="splunk username",
                     default="admin")
    parser.addoption("--splunk-password",
                     help="splunk user password",
                     default="notchangeme")
    parser.addoption("--docker-plugin-path",
                     help="docker plugin binary path",
                     default="/home/ec2-user/plugin/splunk-log-plugin")
    parser.addoption("--fifo-path",
                     help="full file path to the fifo",
                     default="/home/ec2-user/pipe")


@pytest.fixture(scope="function")
def setup(request):
    config = {}
    config["splunkd_url"] = request.config.getoption("--splunkd-url")
    config["splunk_user"] = request.config.getoption("--splunk-user")
    config["splunk_password"] = request.config.getoption("--splunk-password")
    config["plugin_path"] = request.config.getoption("--docker-plugin-path")
    config["fifo_path"] = request.config.getoption("--fifo-path")

    kill_logging_plugin(config["plugin_path"])
    start_logging_plugin(config["plugin_path"])
    time.sleep(2)
    request.addfinalizer(lambda: teardown_method(config["plugin_path"]))

    return config


def teardown_method(plugin_path):
    kill_logging_plugin(plugin_path)
