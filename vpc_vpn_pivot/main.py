import sys
import argparse

from vpc_vpn_pivot.create import create
from vpc_vpn_pivot.connect import connect
from vpc_vpn_pivot.disconnect import disconnect
from vpc_vpn_pivot.purge import purge


DESCRIPTION = '''\
This tool simplifies the creation of an AWS Client VPN with the objective
of connecting to AWS services, such as EC2 instances, which are not 
accessible from the Internet.
'''


def parse_args():
    #
    # Create the top-level parser
    #
    parser = argparse.ArgumentParser(prog='vpc-vpn-pivot',
                                     description=DESCRIPTION)
    subparsers = parser.add_subparsers(help='-',
                                       dest='subcommand')

    #
    # Create the parser for the "create" command
    #
    parser_connect = subparsers.add_parser('create',
                                           help='Create the VPN server')

    parser_connect.add_argument('--profile',
                                help='AWS profile name (as stored in ~/.aws/credentials)',
                                required=True)

    parser_connect.add_argument('--subnet-id',
                                help='Subnet ID of the target network to start a connection with',
                                required=True)

    parser_connect.add_argument('--force',
                                help='Force the connect command to run even if there is a previous state',
                                action='store_true',
                                default=False)

    #
    # Create the parser for the "connect" command
    #
    parser_connect = subparsers.add_parser('connect',
                                           help='Connect to the remote VPC')

    #
    # Create the parser for the "disconnect" command
    #
    parser_disconnect = subparsers.add_parser('disconnect',
                                              help='Disconnect from the VPC')

    #
    # Create the parser for the "purge" command
    #
    parser_purge = subparsers.add_parser('purge',
                                         help='Remove all AWS resources')

    cmd_args = ['--help']

    if len(sys.argv) >= 2:
        cmd_args = sys.argv[1:]

    return parser.parse_args(cmd_args)


def main():
    options = parse_args()

    all_commands = {
        'create': create,
        'connect': connect,
        'disconnect': disconnect,
        'purge': purge,
    }

    if options.subcommand not in all_commands:
        print('Unknown sub-command: %s' % options.subcommand)
        return 1

    return all_commands[options.subcommand](options)
