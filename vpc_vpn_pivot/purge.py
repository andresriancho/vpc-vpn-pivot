import boto3
import shutil

from vpc_vpn_pivot.state import State
from vpc_vpn_pivot.easyrsa import EASYRSA_PATH


def purge(options):
    """
    Remove all the AWS resources

    :param options: Options passed as command line arguments by the user
    :return: Return code
    """
    state = State()

    if not state.dump():
        print('The state file is empty. Call `create` first.')
        return 1

    #
    # The opposite of create_aws_resources()
    #
    overall_success = True
    purge_steps = [
        delete_client_vpn_endpoint,
        delete_acm_certs,
        delete_easy_rsa_install,
    ]

    for purge_step in purge_steps:
        success = purge_step()

        if not success:
            overall_success = False

    if overall_success:
        state.force({})

    return 0


def delete_easy_rsa_install():
    shutil.rmtree(EASYRSA_PATH, ignore_errors=True)
    return True


def delete_acm_certs():
    """
    Delete ACM certificates created during `create`

    :return: True if all certs were removed
    """
    state = State()

    session = boto3.Session(profile_name=state.get('profile'),
                            region_name='us-east-1')
    acm_client = session.client('acm')

    server_arn = state.get('server_cert_acm_arn')
    client_arn = state.get('client_cert_acm_arn')

    server_arn_success = True
    client_arn_success = True

    if server_arn is not None:
        try:
            acm_client.delete_certificate(CertificateArn=server_arn)
        except Exception as e:
            args = (server_arn, e)
            print('Failed to remove ACM server certificate with ARN %s: %s' % args)
            server_arn_success = False
        else:
            print('Removed ACM server certificate with ARN %s' % server_arn)
            state.remove('server_cert_acm_arn')

    if client_arn is not None:
        try:
            acm_client.delete_certificate(CertificateArn=client_arn)
        except Exception as e:
            args = (server_arn, e)
            print('Failed to remove ACM client certificate with ARN %s: %s' % args)
            client_arn_success = False
        else:
            print('Removed ACM client certificate with ARN %s' % server_arn)
            state.remove('client_cert_acm_arn')

    return server_arn_success and client_arn_success


def delete_client_vpn_endpoint():
    """
    Delete all resources created during Client VPN `create`

    :return: True if all certs were removed
    """
    state = State()

    session = boto3.Session(profile_name=state.get('profile'),
                            region_name='us-east-1')
    ec2_client = session.client('ec2')

    security_group_id = state.get('security_group_id')
    vpn_endpoint_id = state.get('vpn_endpoint_id')
    subnet_cidr_block = state.get('subnet_cidr_block')
    association_id = state.get('association_id')

    security_group_success = True
    client_vpn_endpoint_success = True
    client_vpn_target_network_success = True
    client_vpn_ingress_success = True

    if vpn_endpoint_id is None or subnet_cidr_block is None:
        print('There is no VPN ingress to revoke')
    else:
        try:
            ec2_client.revoke_client_vpn_ingress(
                ClientVpnEndpointId=vpn_endpoint_id,
                TargetNetworkCidr=subnet_cidr_block,
                RevokeAllGroups=True,
            )
        except Exception as e:
            print('Failed to delete client VPN ingress: %s' % e)
            client_vpn_ingress_success = False
        else:
            print('Successfully removed client VPN ingress')

    if association_id is None:
        print('There is no VPN association ID to delete')
    else:
        try:
            ec2_client.disassociate_client_vpn_target_network(
                ClientVpnEndpointId=vpn_endpoint_id,
                AssociationId=association_id
            )
        except Exception as e:
            args = (association_id, e)
            print('Failed to delete client VPN association with ID %s: %s' % args)
            client_vpn_target_network_success = False
        else:
            print('Successfully removed client VPN association with ID %s' % association_id)
            state.remove('association_id')

    if vpn_endpoint_id is None:
        print('There is no client VPN endpoint to delete')
    else:
        try:
            ec2_client.delete_client_vpn_endpoint(ClientVpnEndpointId=vpn_endpoint_id)
        except Exception as e:
            args = (vpn_endpoint_id, e)
            print('Failed to delete client VPN endpoint with ID %s: %s' % args)
            client_vpn_endpoint_success = False
        else:
            print('Successfully removed client VPN endpoint with ID %s' % vpn_endpoint_id)
            state.remove('vpn_endpoint_id')

    if security_group_id is None:
        print('There is no security group to remove')
    else:
        try:
            ec2_client.delete_security_group(
                GroupId=security_group_id
            )
        except Exception as e:
            args = (security_group_id, e)
            print('Failed to delete resource with ARN %s: %s' % args)
            security_group_success = False
        else:
            print('Successfully removed resource with ARN %s' % security_group_id)
            state.remove('security_group_id')

    return (security_group_success and
            client_vpn_endpoint_success and
            client_vpn_target_network_success and
            client_vpn_ingress_success)
