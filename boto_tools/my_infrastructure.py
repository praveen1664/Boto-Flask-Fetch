import boto_queries


def find_my_nat(region, instance=None, vpc_id=None):
    """

    :param region: 
    :param instance: 
    :param vpc_id: 
    :return: 
    """

    # ec2_instance accepts an instance ID or Name tag value
    try:
        if not vpc_id:
            vpc_id = instance.vpc_id
        if not vpc_id:
            raise Exception("No VPC found")
    except Exception as e:
        print(str(e))
        return

    print('Searching for NAT in VPC: ' + vpc_id)

    filters = [{'Name': 'vpc-id', 'Values': [vpc_id]},
               {'Name': 'instance-state-name', 'Values': ['running']}]

    # see boto3 documentation for filter formatting
    reservations = boto_queries.ec2_client(filters, region)
    public_ips = {}
    for i in reservations:

        tags = i['Instances'][0].get('Tags')

        # Loop thru the tags of this instance and extract
        # the instance matching 'nat' or 'bastion'
        if tags:
            for t in tags:

                value = t['Value'].lower()  # Instance tag VALUE
                # Search all
                # natkw = ['bastion','nat']
                natkw = ['nat']
                if any(kw in value for kw in natkw):
                    public_ip = i['Instances'][0].get('PublicIpAddress')
                    if public_ip:
                        # return publicIp
                        if public_ips.get('nat') is not None:
                            servertype = extract(key="Server_type", tags=tags)
                            if servertype == "nat":
                                public_ips.update({'nat': public_ip})
                        else:
                            public_ips.update({'nat': public_ip})

                natkw = ['bastion']
                if any(kw in value for kw in natkw):
                    public_ip = i['Instances'][0].get('PublicIpAddress')
                    if public_ip:
                        # return publicIp
                        public_ips.update({'bastion': public_ip})

    try:
        if public_ips.get('bastion'):
            return public_ips.get('bastion')
        if public_ips.get('nat'):
            return public_ips.get('nat')
    except Exception as e:
        print(str(e))

    return None


def extract(instance=None, key=None, tags=None):
    """

    :param instance: boto3 instance client instance 
    :param key: string
    :param tags: 
    :return: 
    """

    try:
        if not tags:
            tags = instance.tags
            print("Tags not passed to extract method")

        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
    except Exception as e:
        print(str(e))
    return
