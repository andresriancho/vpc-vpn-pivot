import re
import os
import subprocess


def run_cmd(cmd, cwd='.', env=None):
    """
    Runs a command using the shell and return the output.

    :param cmd: The command to run
    :param cwd: Path where the command should be run
    :param env: The environment variables to use
    :return: A tuple containing:
                * return code
                * stdout
                * stderr
    """
    completed_process = subprocess.run(cmd,
                                       shell=True,
                                       cwd=cwd,
                                       check=False,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       env=env)

    return (completed_process.returncode,
            completed_process.stdout,
            completed_process.stderr)


def is_valid_vpc_id(vpc_id):
    """
    Validate VPC identifiers

    Example valid IDs:
        - vpc-7128c20c
        - vpc-079cac0a61aaac7a7

    :param vpc_id: The VPC ID to validate
    :return: True if the VPC ID is valid
    """
    return bool(re.match('^vpc-([a-f0-9]{8}|[a-f0-9]{17})$', vpc_id))


def is_valid_subnet_id(vpc_id):
    """
    Validate subnet identifiers

    Example valid IDs:
        - subnet-0d326f29e157a5b79
        - subnet-27f3c340

    :param vpc_id: The VPC ID to validate
    :return: True if the VPC ID is valid
    """
    return bool(re.match('^subnet-([a-f0-9]{8}|[a-f0-9]{17})$', vpc_id))


def read_file_b(filename):
    return open(filename, 'rb').read()


def read_file(filename):
    return open(filename, 'r').read()


def is_root():
    """
    :return: True when the user running the command is root
    """
    if os.geteuid() == 0:
        return True

    return False
