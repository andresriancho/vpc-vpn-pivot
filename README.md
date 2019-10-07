## Pivoting into VPC networks

This tool automates the creation of a VPN between the attacker's workstation and an AWS resource
in the target VPC with the objective of connecting to other AWS services, such as EC2 instances,
which are not accessible from the Internet. 

## Use case

You are performing a cloud penetration test and gained access to a set of 
AWS credentials. The target infrastructure uses VPCs and most of the interesting
services are private (can only be accessed by other hosts connected to the same VPC).

This tool completely automates the process of creating a VPN between your workstation
and the target VPC so you can connect to those private services.

Depending on the permissions associated with the compromised credentials the tool
will use different techniques to create and maintain the VPN service running. For
example, if the credentials have permissions for EC2 and ACM then an [AWS Client VPN](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/cvpn-getting-started.html)
is created and the `openvpn` client is used to connect to it.

## Supported services

This tool will try to create the VPN connection using different techniques, based
on the permissions associated with the compromised credentials. The supported services
for creating the VPN are:

 * [AWS Client VPN](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/cvpn-getting-started.html)
 * EC2
 * Lambda
 * LightSail
 * Fargate
 
## Security groups

`vpc-vpn-pivot` will also try to modify the security groups for all the AWS
resources in the target VPC in such a way that allows you to connect to them.

For example, if there is an RDS database with a security group which only allows
the application server to connect to it, this tool will add a rule to allow
the VPN CIDR to connect to it.

## Noise

The tool will generate a lot of CloudTrail logs and if anyone is paying attention
you will get detected and blocked.

## Installation

The `vpc-vpn-pivot` tool uses Python 3.6. The full installation steps are:

```
git clone https://github.com/andresriancho/vpc-vpn-pivot.git
cd vpc-vpn-pivot
pip3 install requirements.txt
sudo apt-get install openvpn
```

## Usage

This command will setup the SSL certificates, routes and other resources
required for the client VPN to work:

```
./vpc-vpn-pivot create --profile={profile-name} --subnet-id={subnet-id}
```

The `profile` needs to contain compromised credentials for the target AWS account and
be stored in `~/.aws/credentials/`, the VPC ID can be obtained using `aws ec2 describe-vpcs`.


Everything is ready! Just connect your workstation to the VPC using `openvpn`:

```
sudo ./vpc-vpn-pivot connect

./vpc-vpn-pivot status
route -n
nmap -sS ...
```

The script needs to be run using `sudo` because `openvpn` requires root privileges
to create the `tun` interface.

Once connected to the VPC you should be able to inspect the IP address range with
`ifconfig` and run any tool, such as `nmap` to find open services on the VPC.

Use the following commands to disconnect from the VPN and remove all remote
resources created for the VPN to work:

```
./vpc-vpn-pivot disconnect
./vpc-vpn-pivot purge
```

## Troubleshooting

`vpc-vpn-pivot` keeps current state and the names of all the created resources in the
state file (`~/.vpc-vpn-pivot/state`). This file is useful if you need to manually kill
the `openvpn` process or remove the AWS resources.
