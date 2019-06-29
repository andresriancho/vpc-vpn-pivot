from vpc_vpn_pivot.state import State, STATE_FILE


def create(options):
    """
    Create the VPN server in the VPC

    :param options: Options passed as command line arguments by the user
    :return: Return code
    """
    state = State()

    #
    # Check if there is a state and require the user to use --force in order to
    # remove it
    #
    state.get()

    if state and not options.force:
        print('The state file at %s is not empty.\n'
              '\n'
              'This is most likely because the `purge` sub-command was not run'
              ' and the target AWS account could still have resources associated'
              ' with a previous call to `connect`.\n'
              '\n'
              'Use the `purge` sub-command to remove all the remote resources'
              ' or `connect --force` to ignore this situation and run the connect'
              ' process anyways.' % STATE_FILE)
        return 1

    #
    # The first thing we want to do in the connect() is to save the profile
    # passed as parameter to the state. We do this in order to spare the user
    # the need of specifying the same parameter for all the subcommands
    #
    state.append('profile', options.profile)

    raise NotImplementedError