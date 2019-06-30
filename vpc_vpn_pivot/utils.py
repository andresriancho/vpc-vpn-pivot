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
