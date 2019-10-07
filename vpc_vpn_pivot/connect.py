import os
import time
import tempfile
import subprocess

from vpc_vpn_pivot.state import State
from vpc_vpn_pivot.utils import is_root


OPENVPN_CMD = ['openvpn', '--auth-nocache', '--config']


def connect(options):
    """
    Connect to the VPN server

    :param options: Options passed as command line arguments by the user
    :return: Return code
    """
    if not validate(options):
        return 1

    state = State()

    openvpn_config_file = state.get('openvpn_config_file')
    openvpn_config_file = customize_openvpn_config(openvpn_config_file)

    openvpn_filename = write_config_file(openvpn_config_file)

    try:
        connect_to_vpn_server(openvpn_filename)
    except Exception as e:
        print('Unexpected exception while connecting to VPN server: %s' % e)
        os.remove(openvpn_filename)
        return 1
    else:
        os.remove(openvpn_config_file)

    return 0


def validate(options):
    """
    :param options: Options passed as command line arguments by the user
    :return:
    """
    if not is_root():
        print('This command requires root privileges on your system in order'
              ' to run the OpenVPN client in the background.')
        return False

    state = State()

    if not state.dump():
        print('The state file is empty. Call `create` first.')
        return False

    openvpn_config_file = state.get('openvpn_config_file')
    if openvpn_config_file is None:
        print('The `create` command did not save the `openvpn_config_file`'
              ' attribute to the state file.\n'
              '\n'
              'Try to re-generate the VPN connection by running `purge` and'
              ' `create`.')
        return False

    return True


def connect_to_vpn_server(openvpn_filename):
    cmd = OPENVPN_CMD[:]
    cmd.append(openvpn_filename)

    # TODO: Save the stdout and stderr from this command to a log file for
    #       easier debugging?
    process = subprocess.Popen(cmd)

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print('Closing OpenVPN connection...')
        # Termination with Ctrl+C
        try:
            # TODO: Is there a better signal to send to OpenVPN
            #       in order for it to cleanly finish?
            process.kill()
        except:
            pass

        while process.poll() != 0:
            time.sleep(1)

        print('OpenVPN connection closed')


def write_config_file(openvpn_config_file):
    """
    Write the config file to disk

    :param openvpn_config_file: The openvpn config file contents
    :return: The filename where the config was written to
    """
    temp = tempfile.NamedTemporaryFile(mode='w+b',
                                       suffix='.ovpn',
                                       prefix='vpc-vpn-pivot-',
                                       delete=False)

    temp.write(openvpn_config_file)
    return temp.name


def customize_openvpn_config(openvpn_config_file):
    """
    Add some custom config to the OpenVPN config provided by AWS

    :param openvpn_config_file: The OpenVPN config provided by AWS
    :return: The updated config file contents
    """
    openvpn_config_file += '\n\n'
    openvpn_config_file += 'script-security 2\n'

    # TODO: This might only work on Ubuntu, do we need to implement it for
    #       other distributions?
    if os.path.exists('/etc/openvpn/update-resolv-conf'):
        openvpn_config_file += 'up /etc/openvpn/update-resolv-conf\n'
        openvpn_config_file += 'down /etc/openvpn/update-resolv-conf\n'

    return openvpn_config_file
