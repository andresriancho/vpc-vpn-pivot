from vpc_vpn_pivot.state import State


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

    raise NotImplementedError
