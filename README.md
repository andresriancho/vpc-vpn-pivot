## Pivoting into VPC networks

This tool simplifies the creation of an [AWS Client VPN](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/cvpn-getting-started.html)
with the objective of connecting to AWS services, such as EC2 instances, which are not 
accessible from the Internet.

## Use case

You are performing a cloud penetration test and gained access to a set of 
privileged AWS credentials. The target infrastructure uses VPCs and most of
the interesting services are private (can only be accessed by other hosts
connected to the VPC).

This tool simplifies the process of creating a new [AWS Client VPN](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/cvpn-getting-started.html)
and connecting to it using the `openvpn` client.

## Installation

The `vpc-vpn-pivot` tool uses Python3. The full installation steps are:

```
git clone https://github.com/andresriancho/vpc-vpn-pivot.git
cd vpc-vpn-pivot
pip3 install requirements.txt
sudo apt-get install openvpn easy-rsa
```

## Usage

This command will setup the SSL certificates, routes and other resources
required for the client VPN to work:

```
./vpc-vpn-pivot create --profile={profile-name} --vpc-id={vpc-id}
```

The `profile` needs to contain compromised credentials for the target AWS account and
be stored in `~/.aws/credentials/`, the VPC ID can be obtained using `aws ec2 describe-vpcs`.


Everything is ready! Just connect your workstation to the VPC using `openvpn`:

```
sudo ./vpc-vpn-pivot connect
```

The script needs to be run using `sudo` because `openvpn` requires root privileges
to create the `tun` interface.

Once connected to the VPC you should be able to inspect the IP address range with
`ifconfig` and run any tool, such as `nmap` to find open services on the VPC.

Use the following commands to disconnect from the VPN and remove all remote
resources:

```
./vpc-vpn-pivot disconnect
./vpc-vpn-pivot purge
```

## Troubleshooting

`vpc-vpn-pivot` keeps current state and the names of all the created resources in the
state file (`~/.vpc-vpn-pivot/state`). This file is useful if you need to manually kill
the `openvpn` process or remove the AWS resources.
