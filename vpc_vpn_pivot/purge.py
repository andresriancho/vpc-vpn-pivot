from vpc_vpn_pivot.state import State


def purge(options):
    """
    Remove all the AWS resources

    :param options: Options passed as command line arguments by the user
    :return: Return code
    """
    state = State()

    if not state.get():
        print('The state file is empty. Call `create` first.')
        return 1

    raise NotImplementedError
