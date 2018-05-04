
import bridge
from perftestshared.utilities import proc_monitor


PLUGIN_NAME = 'splunk/docker-logging-plugin:latest'
PLUGIN_DIR = 'docker-logging-plugin'
BRANCH = 'develop'
PROCESSES = ["splunk-logging-plugin", "dockerd"]

DGS_MSG_SIZE = 512
DEFAULT_MSG_COUNT = 10000000
DGA_EPS=0
DEFAULT_CONTAINER_COUNT=1
GZIP="false"
FORMAT="inline"
GZIP_LEVEL=-1


class DockerPluginTest(object):

    def deploy_and_enable_plugin(self, working_dir, control_logger):
        """
            Installs the docker plugin on the node
        :param control_logger:
        :return:
        """
        command = ["echo", "eserv", "|", "sudo", "-S", "sh", "deploy_and_enable_plugin.sh"]
        br = bridge.Bridge(control_logger)
        br.execute_single_command(command, working_dir=working_dir)

    def _run_test(
            self,
            hec_url,
            hec_token,
            hec_source,
            hec_sourcetype,
            control_logger,
            message_count=DEFAULT_MSG_COUNT,
            container_count=1
    ):
        br = bridge.Bridge(control_logger)

        # Test command arguments
        cmd = [
            "echo",
            "eserv",
            "|",
            "sudo",
            "-S","docker",
            "run",
            ("--log-driver=%s" % PLUGIN_NAME),
            "--log-opt",
            "splunk-gzip-level=-1",
            "--log-opt",
            "tag=\"{{.Name}}/{{.FullID}}\"",
            "--log-opt",
            "splunk-gzip=false",
            "--log-opt",
            "splunk-url={}".format(hec_url),
            "--log-opt",
            "splunk-token={}".format(hec_token),
            "--log-opt",
            "splunk-source={}".format(hec_source),
            "--log-opt",
            "splunk-sourcetype={}".format(hec_sourcetype),
            "--log-opt",
            "splunk-insecureskipverify=true",
            "-d",
            "-e",
            "MSG_COUNT={}".format(str(message_count)),
            "-e",
            "MSG_SIZE={}".format(str(DGS_MSG_SIZE)),
            "-e",
            "EPS={}".format(str(DGA_EPS)),
            "luckyj5/docker-datagen"
        ]

        for i in range(container_count):
            control_logger.info("Running test with command: %s" % ' '.join(cmd))

            # TODO: implement blocking for docker
            br.execute_single_command(cmd)

    def run_sizing_guide_test(
            self,
            hec_url,
            hec_token,
            hec_source,
            hec_sourcetype,
            control_logger,
            container_count,
            message_count
    ):
        self._run_test(
            hec_url,
            hec_token,
            hec_source,
            hec_sourcetype,
            control_logger,
            message_count=message_count,
            container_count=container_count
        )


def run_test(
        hec_url,
        hec_token,
        hec_source,
        hec_sourcetype,
        control_logger,
        message_count=DEFAULT_MSG_COUNT,
        container_count=1
    ):
    br = bridge.Bridge(control_logger)

    # Test command arguments
    cmd = [
        "echo",
        "eserv",
        "|",
        "sudo",
        "-S","docker",
        "run",
        ("--log-driver=%s" % PLUGIN_NAME),
        "--log-opt",
        "splunk-gzip-level=-1",
        "--log-opt",
        "tag=\"{{.Name}}/{{.FullID}}\"",
        "--log-opt",
        "splunk-gzip=false",
        "--log-opt",
        "splunk-url={}".format(hec_url),
        "--log-opt",
        "splunk-token={}".format(hec_token),
        "--log-opt",
        "splunk-source={}".format(hec_source),
        "--log-opt",
        "splunk-sourcetype={}".format(hec_sourcetype),
        "--log-opt",
        "splunk-insecureskipverify=true",
        "-d",
        "-e",
        "MSG_COUNT={}".format(str(message_count)),
        "-e",
        "MSG_SIZE={}".format(str(DGS_MSG_SIZE)),
        "-e",
        "EPS={}".format(str(DGA_EPS)),
        "luckyj5/docker-datagen"
    ]

    for i in range(container_count):
        control_logger.info("Running test with command: %s" % ' '.join(cmd))
        br.execute_single_command(cmd)


class MonitorPlugin(object):

    def monitor_processes(self, processes):
        proc_monitor.collect_metrics(
            processes
        )

        return {
            'data': 'FROM MONITOR'
        }
