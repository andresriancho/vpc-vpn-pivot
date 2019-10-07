import psutil

from vpc_vpn_pivot.state import State
from vpc_vpn_pivot.connect import OPENVPN_LOG_FILE


def status(options):

    state = State()

    openvpn_pid = state.get('openvpn_pid')
    if openvpn_pid is None:
        print('The VPN connection was never initiated. Call the `connect` sub-command')
        return 1

    try:
        p = psutil.Process(openvpn_pid)
    except psutil.NoSuchProcess:
        print('The OpenVPN process died! Check the %s log file' % OPENVPN_LOG_FILE)
        return 1

    if p.name() != 'openvpn':
        print('The OpenVPN process died! Check the %s log file' % OPENVPN_LOG_FILE)
        return 1

    print('The VPN connection is alive')
    return 0
