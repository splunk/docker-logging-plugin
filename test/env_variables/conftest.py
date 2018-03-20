
import pytest
from common import kill_logging_plugin


@pytest.fixture(scope="function")
def setup(request):
    '''
    This is an override of the fixture in the test root.

    When testing env variables, the logging plugin needs to start after
    the environment variables are set
    '''
    config = {}
    config["splunkd_url"] = request.config.getoption("--splunkd-url")
    config["splunk_hec_url"] = request.config.getoption("--splunk-hec-url")
    config["splunk_hec_token"] = request.config.getoption("--splunk-hec-token")
    config["splunk_user"] = request.config.getoption("--splunk-user")
    config["splunk_password"] = request.config.getoption("--splunk-password")
    config["plugin_path"] = request.config.getoption("--docker-plugin-path")
    config["fifo_path"] = request.config.getoption("--fifo-path")

    kill_logging_plugin(config["plugin_path"])
    request.addfinalizer(lambda: teardown_method(config["plugin_path"]))

    return config


def teardown_method(plugin_path):
    kill_logging_plugin(plugin_path)
