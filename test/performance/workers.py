import os

import bridge
import proc_monitor

# Default working dir: '/mnt/ephemeral0/test
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

    def deploy_and_enable_plugin(self, control_logger):
        """
            Installs the docker plugin on the node
        :param control_logger:
        :return:
        """

        commands = [
            ["echo", "eserv", "|", "sudo","-S", "apt-get", "update", "-y"],
            ["curl", "-fsSL", "get.docker.com", "-o", "get-docker.sh"],
            ["echo", "eserv", "|", "sudo", "-S", "sh", "get-docker.sh"],
            ["echo", "eserv", "|", "sudo","-S","usermod", "-a", "-G", "docker", "eserv"],
            ["echo", "eserv", "|", "sudo","-S","apt-get", "install", "make", "-y"]

        ]

        br = bridge.Bridge(control_logger)
        br.execute_commands(commands)

        # Install docker plugin
        self._install_plugin(control_logger)

    def _install_plugin(self, control_logger):

        """
        1- clone repo
        2- cd
        git clone https://github.com/splunk/docker-logging-plugin.git;
        cd docker-logging-plugin;
        git checkout develop
        make
        docker plugin enable splunk-log-plugin
        """
        # clone repo
        br = bridge.Bridge(control_logger)
        control_logger.info("Cloning plugin repo")
        cmd_clone = ["git", "clone", "https://github.com/splunk/docker-logging-plugin.git"]

        br.execute_single_command(cmd_clone)

        # TODO: workaround branch, remove once issue is fixed
        plugin_dir = os.path.abspath(os.path.normpath(os.path.join(os.getcwd(), PLUGIN_DIR)))
        branch = 'fix-partial-msg-isse'
        cmd_checkout = ['git', 'checkout', 'fix-partial-msg-isse']
        br.execute_single_command(cmd_checkout,working_dir=plugin_dir)

        # run make command
        control_logger.info("Installing plugin with Make")
        cmd_make = ["echo", "eserv", "|", "sudo","-S", "make"]
        br.execute_single_command(cmd_make,working_dir=plugin_dir)

        # Enable plugin
        cmd_make.append('enable')
        control_logger.info("Enabling plugin!")
        br.execute_single_command(cmd_make,working_dir=plugin_dir)


    def run_throughput_test(
            self,
            hec_url,
            hec_token,
            hec_source,
            hec_sourcetype,
            control_logger,
            message_count=DEFAULT_MSG_COUNT
    ):

        self._run_test(
            hec_url,
            hec_token,
            hec_source,
            hec_sourcetype,
            control_logger,
            message_count=message_count
        )

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


class SizingGuideTest(object):
    def run_guideline_test(
            self,
            hec_url,
            hec_token,
            hec_source,
            hec_sourcetype,
            control_logger,
            container_count,
            message_count
    ):
        run_test(
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

    def monitor_process(self, processes, hec_url, hec_token):
        proc_monitor.collect_process_data(
            processes,
            hec_url=hec_url,
            hec_token=hec_token
        )

        return {
            'data': 'FROM MONITOR'
        }


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
            br.execute_single_command(cmd)
