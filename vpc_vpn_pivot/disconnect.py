import os
import signal

from vpc_vpn_pivot.state import State
from vpc_vpn_pivot.utils.misc import is_root


def disconnect(options):
    """
    Disconnect from the VPN, leaving all AWS resources intact.

    :param options: Options passed as command line arguments by the user
    :return: Return code
    """
    state = State()

    if not state.dump():
        print('The state file is empty. Call `create` first.')
        return 1

    if not is_root():
        print('You need root privileges to kill the openvpn process.')
        return 1

    openvpn_pid = state.get('openvpn_pid')
    if openvpn_pid is None:
        print('The VPN connection was never initiated.')
        return 1

    os.kill(openvpn_pid, signal.SIGINT)

    print('Ctrl+C sent to the OpenVPN client process')

    state.remove('openvpn_pid')

    return 0
