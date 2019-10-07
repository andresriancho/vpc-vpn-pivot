import os
import time
import shlex
import tempfile
import subprocess

from vpc_vpn_pivot.state import State
from vpc_vpn_pivot.utils.misc import is_root, read_file
from vpc_vpn_pivot.utils.which import which
from vpc_vpn_pivot.utils.tail import tail

OPENVPN_LOG_FILE = 'openvpn.log'

OPENVPN_PARAMS = [
    '--auth-nocache',
    '--log %s' % OPENVPN_LOG_FILE,
]


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
        os.remove(openvpn_filename)

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

    openvpn_executables = which('openvpn')
    if not openvpn_executables:
        print('This command requires `openvpn` to be installed in your'
              ' system.')
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
    state = State()

    params = OPENVPN_PARAMS[:]
    params.append('--config %s' % openvpn_filename)

    openvpn_executable = which('openvpn')[0]

    cmd = [openvpn_executable]
    cmd.extend(params)
    cmd = shlex.split(' '.join(cmd))

    process = subprocess.Popen(cmd,
                               close_fds=True)

    print('OpenVPN client started in process %s' % process.pid)
    print('VPN connection log is at %s' % OPENVPN_LOG_FILE)

    state.append('openvpn_pid', process.pid)

    time.sleep(5)

    print('\nLast five lines from connection log:')
    log_lines = tail(open(OPENVPN_LOG_FILE), 5)
    log_lines = '    '.join(log_lines)
    print(log_lines)

    return True


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

    temp.write(openvpn_config_file.encode('utf-8'))
    temp.flush()

    return temp.name


def customize_openvpn_config(openvpn_config_file):
    """
    Add some custom config to the OpenVPN config provided by AWS

    :param openvpn_config_file: The OpenVPN config provided by AWS
    :return: The updated config file contents
    """
    openvpn_config_file = add_script_security(openvpn_config_file)
    openvpn_config_file = add_update_resolv(openvpn_config_file)
    openvpn_config_file = add_certs(openvpn_config_file)
    return openvpn_config_file


def add_script_security(openvpn_config_file):
    openvpn_config_file += '\n\n'
    openvpn_config_file += 'script-security 2\n'
    return openvpn_config_file


def add_update_resolv(openvpn_config_file):
    openvpn_config_file += '\n\n'

    # TODO: This might only work on Ubuntu, do we need to implement it for
    #       other distributions?
    if os.path.exists('/etc/openvpn/update-resolv-conf'):
        openvpn_config_file += 'up /etc/openvpn/update-resolv-conf\n'
        openvpn_config_file += 'down /etc/openvpn/update-resolv-conf\n'

    return openvpn_config_file


def add_certs(openvpn_config_file):
    cert_fmt = '\n\n<cert>\n%s\n</cert>\n'
    key_fmt = '\n\n<key>\n%s\n</key>\n'

    state = State()

    openvpn_config_file += cert_fmt % read_file(state.get('client_crt').encode('utf-8'))
    openvpn_config_file += key_fmt % read_file(state.get('client_key').encode('utf-8'))

    return openvpn_config_file
