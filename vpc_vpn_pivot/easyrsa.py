import os
import shutil
import tarfile
import requests

from vpc_vpn_pivot.utils import run_cmd
from vpc_vpn_pivot.constants import CA_PATH

EASYRSA_RELEASE = 'https://github.com/OpenVPN/easy-rsa/releases/download/v3.0.6/EasyRSA-unix-v3.0.6.tgz'
EASYRSA_PATH = '/tmp/EasyRSA-v3.0.6/'
EASYRSA_COMPRESSED = '/tmp/EasyRSA-unix-v3.0.6.tgz'


def remove_previous_install():
    paths_to_remove = (
        EASYRSA_PATH,
        EASYRSA_COMPRESSED
    )

    for path_to_remove in paths_to_remove:
        try:
            shutil.rmtree(path_to_remove)
        except:
            continue


def install_easyrsa():
    #
    # Download and decompress
    #
    try:
        r = requests.get(EASYRSA_RELEASE)
    except Exception as e:
        print('Failed to download EasyRSA: %s' % e)
        return False

    with open(EASYRSA_COMPRESSED, 'wb') as f:
        f.write(r.content)

    tf = tarfile.open(EASYRSA_COMPRESSED)
    tf.extractall(path='/tmp/')

    return True


def cert_path(filename):
    return os.path.join(CA_PATH, filename)


def create_vpn_certs():
    """
    Create all SSL certs required for the VPN connection and return the fs
    paths.

    https://github.com/aws-quickstart/quickstart-biotech-blueprint/blob/f2e1e76dc8cbc30fd938dd78f0ea5c029c03a9d4/scripts/clientvpnendpoint-customlambdaresource.py#L63-L72

    :return: A tuple containing paths to:
                * ca.crt
                * server.crt
                * server.key
                * client.crt
                * client.key
    """
    create_certs_commands = [
        './easyrsa init-pki',
        './easyrsa build-ca nopass',
        './easyrsa build-server-full server nopass',
        './easyrsa build-client-full client.domain.tld nopass'
    ]

    env = os.environ.copy()
    env['EASYRSA_BATCH'] = '1'

    for cmd in create_certs_commands:
        return_code, stdout, stderr = run_cmd(cmd, cwd=EASYRSA_PATH, env=env)

        if return_code != 0:
            print('The "%s" command failed!' % cmd)
            print('')
            print(stdout)
            print(stderr)
            return False

    return (cert_path('ca.crt'),
            cert_path('issued/server.crt'),
            cert_path('private/server.key'),
            cert_path('issued/client.domain.tld.crt'),
            cert_path('private/client.domain.tld.key'))
