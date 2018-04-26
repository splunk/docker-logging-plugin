import os
import subprocess


class Bridge(object):

    def __init__(self, control_logger):
        self.logger = control_logger

    def execute_commands(self, commands, working_dir=None):
        """
            Executes a collection of sell commands
        :param commands:
        :param working_dir:
        :return:
        """
        for cmd in commands:
            self.execute_single_command(cmd)

    def execute_single_command(self, command, working_dir=None):
        """
            Executes a single shell command in form of string to shell
        :param command: list or string
        :param working_dir:
        :return:
        """
        cmd = command
        if isinstance(command, list):
            cmd = ' '.join(command)

        if working_dir:
            os.chdir(working_dir)
        self.logger.info("Started command: %s" % cmd)
        p = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        out, err = p.communicate()
        self.logger.info(out)
        if err is not None:
            self.logger.error(err)
        else:
            self.logger.info("Command: %s completed!" % cmd)

        return out, err
