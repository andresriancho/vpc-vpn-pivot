from vpc_vpn_pivot.state import State
from vpc_vpn_pivot.ssl.easyrsa import (remove_previous_install,
                                       install_easyrsa,
                                       create_vpn_certs)


def create_ssl_certs(options):
    """
    Create the SSL certificates using easyrsa

    :param options: Options passed as command line arguments by the user
    :return: True if all the SSL certs were successfully created
    """
    #
    # Cleanup
    #
    remove_previous_install()

    #
    # Install EasyRSA
    #
    success = install_easyrsa()

    if not success:
        return False

    #
    # Create VPN certs
    #
    result = create_vpn_certs()

    if not result:
        return False

    ca_crt = result[0]
    server_crt = result[1]
    server_key = result[2]
    client_crt = result[3]
    client_key = result[4]

    state = State()

    state.append('ca_crt', ca_crt)
    state.append('server_crt', server_crt)
    state.append('server_key', server_key)
    state.append('client_crt', client_crt)
    state.append('client_key', client_key)

    print('Successfully created SSL certificates for the VPN')

    return True
