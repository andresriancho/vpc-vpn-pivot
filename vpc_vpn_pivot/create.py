import re
import boto3

from botocore.exceptions import ClientError

from vpc_vpn_pivot.state import State
from vpc_vpn_pivot.constants import STATE_FILE
from vpc_vpn_pivot.easyrsa import (remove_previous_install,
                                   install_easyrsa,
                                   create_vpn_certs)


def is_valid_vpc_id(vpc_id):
    """
    Validate VPC identifiers

    Example valid ID: vpc-7128c20c

    :param vpc_id: The VPC ID to validate
    :return: True if the VPC ID is valid
    """
    return bool(re.match('vpc-[a-f0-9]{8}', vpc_id))


def create(options):
    """
    Create the VPN server in the VPC

    :param options: Options passed as command line arguments by the user
    :return: Return code
    """
    state = State()

    #
    # Initial checks to increase the chances of success during AWS resource
    # creation
    #
    success = perform_initial_checks(options)

    if not success:
        return 1

    msg = 'Creating VPN server in AWS account ID %s using %s'
    args = (state.get('account_id'),
            state.get('user_arn'))
    print(msg % args)

    #
    # Create the SSL certificates
    #
    success = create_ssl_certs(options)

    if not success:
        return 1

    #
    # Create the AWS resources. Leave this step to the end in order to reduce
    # the number of resources to remove if something fails
    #
    create_aws_resources(options)


def perform_initial_checks(options):
    """
    Perform initial checks on the user-controlled parameters

    :param options: Options passed as command line arguments by the user
    :return: True if all the inputs look good
    """
    state = State()

    #
    # Check if there is a state and require the user to use --force in order to
    # remove it
    #
    if state.dump() and not options.force:
        print('The state file at %s is not empty.\n'
              '\n'
              'This is most likely because the `purge` sub-command was not run'
              ' and the target AWS account could still have resources associated'
              ' with a previous call to `connect`.\n'
              '\n'
              'Use the `purge` sub-command to remove all the remote resources'
              ' or `connect --force` to ignore this situation and run the connect'
              ' process anyways.' % STATE_FILE)
        return False

    if not is_valid_vpc_id(options.vpc_id):
        print('%s does not have a valid VPC ID format' % options.vpc_id)
        return False

    #
    # Check if the profile is valid
    #
    try:
        session = boto3.Session(profile_name=options.profile)
    except Exception:
        print('%s is not a valid profile defined in ~/.aws/credentials' % options.profile)
        return False

    sts_client = session.client('sts')

    try:
        response = sts_client.get_caller_identity()
    except Exception as e:
        msg = ('The profile has invalid credentials.'
               ' Call to get_caller_identity() failed with error: %s')
        print(msg % e)
        return False

    account_id = response['Account']
    arn = response['Arn']

    #
    # Check if the specified VPC ID exists in the target AWS account
    #
    ec2_client = session.client('ec2')

    try:
        ec2_client.describe_vpcs(VpcIds=[options.vpc_id])
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidVpcID.NotFound':
            #
            # Show the error
            #
            msg = 'The specified VPC ID (%s) does not exist in AWS account %s'
            args = (options.vpc_id, account_id)
            print(msg % args)

            #
            # Get the user a list of all the VPC IDs
            #
            print('')
            print('The following is a list of existing VPCs:')
            print('')
            response = ec2_client.describe_vpcs()

            for vpc_data in response['Vpcs']:
                args = (vpc_data['VpcId'], vpc_data['CidrBlock'])
                msg = ' * %s - %s'
                print(msg % args)
        else:
            print('Failed to call ec2.describe_vpcs: %s' % e)

        return False

    #
    # The first thing we want to do in the connect() is to save the profile
    # passed as parameter to the state. We do this in order to spare the user
    # the need of specifying the same parameter for all the subcommands
    #
    state.append('profile', options.profile)
    state.append('account_id', account_id)
    state.append('user_arn', arn)
    state.append('vpc_id', options.vpc_id)

    return True


def create_aws_resources(options):
    """
    Create the AWS resources

    :param options: Options passed as command line arguments by the user
    :return: True if all the resources were successfully created
    """
    raise NotImplementedError


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

    return True
