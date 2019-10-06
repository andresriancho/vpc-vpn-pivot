import boto3

from botocore.exceptions import ClientError

from vpc_vpn_pivot.state import State
from vpc_vpn_pivot.constants import STATE_FILE, DEFAULT_DNS_SERVERS
from vpc_vpn_pivot.ssl.certs import create_ssl_certs
from vpc_vpn_pivot.utils import (is_valid_vpc_id,
                                 is_valid_subnet_id,
                                 read_file)


def create(options):
    """
    Create the VPN server in the VPC

    :param options: Options passed as command line arguments by the user
    :return: Return code

    :see: https://github.com/aws-quickstart/quickstart-biotech-blueprint/blob/f2e1e76dc8cbc30fd938dd78f0ea5c029c03a9d4/scripts/clientvpnendpoint-customlambdaresource.py#L40
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
    success = create_aws_resources(options)

    if not success:
        return 1

    return 0


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

    if not is_valid_subnet_id(options.subnet_id):
        print('%s does not have a valid Subnet ID format' % options.subnet_id)
        return False

    #
    # Check if the profile is valid
    #
    try:
        session = boto3.Session(profile_name=options.profile,
                                region_name='us-east-1')
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
    # Check if the specified Subnet ID exists in the target AWS account
    #
    ec2_client = session.client('ec2')

    try:
        subnets = ec2_client.describe_subnets(SubnetIds=[options.subnet_id])
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidSubnetID.NotFound':
            #
            # Show the error
            #
            msg = 'The specified Subnet ID (%s) does not exist in AWS account %s'
            args = (options.subnet_id, account_id)
            print(msg % args)

            #
            # Get the user a list of all the VPC IDs
            #
            print('')
            print('The following is a list of existing subnets:')
            print('')

            response = ec2_client.describe_subnets()

            for subnet_data in response['Subnets']:
                args = (subnet_data['SubnetId'], subnet_data['CidrBlock'], subnet_data['VpcId'])
                msg = ' - %s (%s , %s)'
                print(msg % args)
        else:
            print('Failed to call ec2.describe_subnets: %s' % e)

        return False

    #
    # We want to get the VPC ID for this subnet and store it
    #
    vpc_id = subnets['Subnets'][0]['VpcId']
    subnet_cidr_block = subnets['Subnets'][0]['CidrBlock']

    args = (options.subnet_id, subnet_cidr_block, vpc_id)
    print('%s has IP address CIDR %s and is in %s' % args)

    #
    # The first thing we want to do in the connect() is to save the profile
    # passed as parameter to the state. We do this in order to spare the user
    # the need of specifying the same parameter for all the sub-commands
    #
    state.append('profile', options.profile)
    state.append('account_id', account_id)
    state.append('user_arn', arn)
    state.append('vpc_id', vpc_id)
    state.append('subnet_id', options.subnet_id)
    state.append('subnet_cidr_block', subnet_cidr_block)

    return True


def create_aws_resources(options):
    """
    Create the AWS resources

    :param options: Options passed as command line arguments by the user
    :return: True if all the resources were successfully created
    """
    success = create_acm_certs(options)

    if not success:
        return False

    success = get_cidr_block(options)

    if not success:
        return False

    success = get_dns_servers(options)

    if not success:
        return False

    success = create_client_vpn_endpoint(options)

    if not success:
        return False

    success = add_cidr_to_all_security_groups(options)

    if not success:
        return False

    return True


def add_cidr_to_all_security_groups(options):
    """
    Adds the VPN CIDR to all security groups that would block traffic.

    If there is a security group with a rule allowing all traffic from all
    sources then no change is applied to that security group.

    If there is a security group allowing traffic coming from only a specific
    IP address then this function adds a rule to allow traffic from the VPN CIDR.

    This is noisy.

    :param options: Options passed as command line arguments by the user
    :return: True if all security groups were modified to allow all traffic from the VPN CIDR
    """
    # TODO: Implement this feature
    return True


def create_acm_certs(options):
    """
    Create the ACM resources

    :param options: Options passed as command line arguments by the user
    :return: True if all the resources were successfully created
    """
    session = boto3.Session(profile_name=options.profile,
                            region_name='us-east-1')
    acm_client = session.client('acm')

    state = State()

    try:
        response = acm_client.import_certificate(
            Certificate=read_file(state.get('server_crt')),
            PrivateKey=read_file(state.get('server_key')),
            CertificateChain=read_file(state.get('ca_crt'))
        )
    except Exception as e:
        print('Failed to import server certificate: %s' % e)
        return False
    else:
        state.append('server_cert_acm_arn', response['CertificateArn'])

    try:
        response = acm_client.import_certificate(
            Certificate=read_file(state.get('client_crt')),
            PrivateKey=read_file(state.get('client_key')),
            CertificateChain=read_file(state.get('ca_crt'))
        )
    except Exception as e:
        print('Failed to import client certificate: %s' % e)
        return False
    else:
        state.append('client_cert_acm_arn', response['CertificateArn'])

    print('Successfully created certificates in ACM')

    return True


def get_cidr_block(options):
    """
    This is the CIDR block for the VPN clients.

    We'll be the only ones connecting to this VPN so a /30 is more than enough,
    but it is very important for us to choose a CIDR block that:

        * Doesn't overlap with the client's local network (usually 192.168.0.0/24
          or 10.0.0.0/16)

        * Doesn't overlap with any of the CIDR blocks defined in the target account,
          blocks defined in VPC peerings, etc.

    Ideally it should be a CIDR block that is adjacent to the VPC CIDR.
    For example if the VPC has 10.0.0.0/24 we should choose 10.0.1.0/30 to benefit
    from potential security groups which are allowing access to 10.0.0.0/16.

    :param options: Options passed as command line arguments by the user
    :return: True if we were able to find a CIDR block for the VPN client
    """
    state = State()
    state.append('cidr_block', '10.2.0.0/16')

    # TODO: Choose a /30 or /29 CIDR block! Larger has more changes of collision

    print('Using CIDR block %s' % state.get('cidr_block'))

    return True


def get_dns_servers(options):
    """
    Get the DNS servers for the VPN connection.

    If the target VPC has a custom set of DNS servers (most likely internal or
    route53 servers) use those. They will allow us to better map the internal
    network.

    If there are no custom DNS servers set in the VPC just use:
        * 1.1.1.1
        * 8.8.8.8

    :param options: Options passed as command line arguments by the user
    :return: True if we were able to get the DNS servers for the VPN
    """
    state = State()

    # TODO: Implement custom DNS according to remote config
    state.append('dns_server_list', DEFAULT_DNS_SERVERS)

    print('Using DNS servers: %s' % ', '.join(state.get('dns_server_list')))

    return True


def create_client_vpn_endpoint(options):
    """
    Create client VPN endpoint

        aws ec2 create-client-vpn-endpoint ...

    :param options: Options passed as command line arguments by the user
    :return: True if all the SSL certs were successfully created
    """
    state = State()

    session = boto3.Session(profile_name=state.get('profile'),
                            region_name='us-east-1')
    ec2_client = session.client('ec2')

    #
    #    aws ec2 create-client-vpn-endpoint
    #
    try:
        response = ec2_client.create_client_vpn_endpoint(
            ClientCidrBlock=state.get('cidr_block'),

            ServerCertificateArn=state.get('server_cert_acm_arn'),

            AuthenticationOptions=[
                {'Type': 'certificate-authentication',
                 'MutualAuthentication': {
                     'ClientRootCertificateChainArn': state.get('client_cert_acm_arn')
                 }}
            ],

            ConnectionLogOptions={
                'Enabled': False,
            },

            DnsServers=state.get('dns_server_list'),

            TransportProtocol='udp',
        )
    except Exception as e:
        print('Failed to create client VPN endpoint: %s' % e)
        return False
    else:
        vpn_endpoint_id = response['ClientVpnEndpointId']
        state.append('vpn_endpoint_id', vpn_endpoint_id)

    #
    #    aws ec2 associate-client-vpn-target-network
    #
    try:
        response = ec2_client.associate_client_vpn_target_network(
            ClientVpnEndpointId=vpn_endpoint_id,
            SubnetId=state.get('subnet_id')
        )
    except Exception as e:
        print('Failed to create client vpn association: %s' % e)
        return False
    else:
        association_id = response['AssociationId']
        state.append('association_id', association_id)

    #
    #   aws ec2 create-client-vpn-route
    #
    try:
        response = ec2_client.create_client_vpn_route(
            ClientVpnEndpointId=vpn_endpoint_id,
            DestinationCidrBlock='0.0.0.0/0',
            TargetVpcSubnetId=state.get('subnet_id'),
            Description='Client VPN route #1',
        )
    except Exception as e:
        print('Failed to create client vpn route: %s' % e)
        return False
    else:
        # TODO: How do I get the route ID to remove it later?
        pass

    #
    #   aws ec2 authorize-client-vpn-ingress
    #
    try:
        response = ec2_client.authorize_client_vpn_ingress(
            ClientVpnEndpointId=vpn_endpoint_id,
            TargetNetworkCidr=state.get('subnet_cidr_block'),
            AuthorizeAllGroups=True,
            Description='Client VPN ingress #1',
        )
    except Exception as e:
        print('Failed to create ingress authorization for vpn client: %s' % e)
        return False
    else:
        # TODO: How do I get the authorization ID to remove it later?
        pass

    #
    #   aws ec2 create-security-group
    #
    try:
        response = ec2_client.create_security_group(
            Description='Security group for client VPN',
            GroupName='client_vpn',
            VpcId=state.get('vpc_id'),
        )

        state.append('security_group_id', response['GroupId'])

        ec2_client.authorize_security_group_ingress(
            GroupId=state.get('security_group_id'),
            IpPermissions=[
                {'IpProtocol': 'tcp',
                 'FromPort': 0,
                 'ToPort': 65535,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'udp',
                 'FromPort': 0,
                 'ToPort': 65535,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        )
    except Exception as e:
        print('Failed to create security group for client vpn network: %s' % e)
        return False
    else:
        # TODO: How do I get the authorization ID to remove it later?
        pass

    #
    #   aws ec2 apply-security-groups-to-client-vpn-target-network
    #
    try:
        response = ec2_client.apply_security_groups_to_client_vpn_target_network(
            ClientVpnEndpointId=vpn_endpoint_id,
            VpcId=state.get('vpc_id'),
            SecurityGroupIds=[
                state.get('security_group_id'),
            ],
        )
    except Exception as e:
        print('Failed to apply security group to client vpn network: %s' % e)
        return False
    else:
        # TODO: How do I get the authorization ID to remove it later?
        pass

    return True
