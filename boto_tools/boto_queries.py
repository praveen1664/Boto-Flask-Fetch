import boto3
import socket
from datetime import datetime


def describe_regions():
    """
    http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_regions
    
    Get a list of all AWS regions
    :return:  
    """
    client = boto3.client("ec2", region_name="us-west-2")  # requires a region
    regions = client.describe_regions()
    return regions["Regions"]


def ec2_client(filters, region):
    """
    http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
    
    :param filters: 
    :param region: 
    :return:
    """
    client = boto3.client('ec2', region_name=region)
    instances = client.describe_instances(Filters=filters)
    return instances['Reservations']


def ec2_instance(instance_id, region, only_id=False):
    """
    Finds the resource by name or Id. Essentially it's the same as
    ec2_client but more specific. Instead of returning multiple instances,
    this will only return one single instance.

    :param instance_id: 
    :param region: 
    :param only_id: 
    :return: Single instance resource
    :return (onlyId): STDOUT String of Instance Id (or None)
    """

    if instance_id.startswith('i-'):
        # No further action needed, this is the ID
        try:
            filters = [{"Name": "instance-id", "Values": [instance_id]}]
            instances = ec2_client(filters, region)
            instance_id = instances[0]["Instances"][0]["InstanceId"]
        except KeyError:
            return
        except IndexError:
            return
    else:

        # Did the user pass in an ip address?
        try:
            socket.inet_aton(instance_id)  # inet_aton checks this is IPv4 addr

            # Did the user pass in a public ip address?
            try:
                if not instance_id.startswith('i-'):
                    filters = [{"Name": "ip-address", "Values": [instance_id]}]
                    instances = ec2_client(filters, region)
                    instance_id = instances[0]["Instances"][0]["InstanceId"]
            except KeyError:
                return
            except IndexError:
                return

            # Did the user pass in a private ip address?
            try:
                if not instance_id.startswith('i-'):
                    filters = [
                        {"Name": "private-ip-address", "Values": [instance_id]}]
                    instances = ec2_client(filters, region)
                    instance_id = instances[0]["Instances"][0]["InstanceId"]
            except KeyError:
                return
            except IndexError:
                return

        except socket.error:  # The user did not pass in an ip address
            pass

        # Did the user pass in an AWS tag:Name
        if not instance_id.startswith('i-'):
            filters = [
                {"Name": "tag:Name", "Values": [instance_id]}]

            instances = ec2_client(filters, region)
            instance_id = instances[0]['Instances'][0]['InstanceId']

    # print instanceId
    if only_id:
        return instance_id

    resource = boto3.resource('ec2', region_name=region)
    return resource.Instance(instance_id)


def filter_resource_tags(filters, resource, tag_list, resource_list,
                         total_matches):
    for tag in tag_list:
        kv = {"Name": tag["Key"], "Values": [tag["Value"]]}
        if kv in filters:
            total_matches += 1
            if len(filters) == total_matches:
                resource_list.append(resource)
                return True
    return False


def filter_elbs(filters, region):
    """

    :param filters: 
    :param region: 
    :return: 
    """
    elb_list = []

    client = boto3.client('elb', region_name=region)
    elbs = client.describe_load_balancers()
    for elb in elbs["LoadBalancerDescriptions"]:
        tags = client.describe_tags(
            LoadBalancerNames=[elb["LoadBalancerName"]])
        total_matches = 0
        elb.update({"TagDescriptions": tags["TagDescriptions"]})
        for tag_description in tags["TagDescriptions"]:
            elb_added = filter_resource_tags(filters,
                                             elb,
                                             tag_description["Tags"],
                                             elb_list,
                                             total_matches)
            if elb_added:
                break
    return elb_list


def filter_vpcs(filters, region):
    """

    :param filters:
    :param region:
    :return:
    """
    client = boto3.client('ec2', region_name=region)
    vpcs = client.describe_vpcs(Filters=filters)
    return vpcs['Vpcs']


def filter_db_instances(filters, region, aws_arn_code):
    """

    :param filters: 
    :param region: 
    :param aws_arn_code:
    :return: 
    """
    rds_list = {}

    client = boto3.client('rds', region_name=region)
    rdss = client.describe_db_instances()
    i = 0
    for rds in rdss["DBInstances"]:
        arn = "arn:aws:rds:{0}:{1}:db:{2}".format(
            region,
            aws_arn_code,
            rds["DBInstanceIdentifier"])
        tags = client.list_tags_for_resource(ResourceName=arn)
        rds.update({"Tags": tags["TagList"]})
        total_matches = 0
        for tag in tags["TagList"]:
            kv = {"Name": tag["Key"], "Values": [tag["Value"]]}
            if kv in filters:
                total_matches += 1
                if len(filters) == total_matches:
                    rds_list.update({i: [rds, tags["TagList"]]})
                    i += 1
                    break
    return rds_list


def filter_elasticache_clusters(filters, region, aws_arn_code):
    """

    :param filters: 
    :param region: 
    :param aws_arn_code:
    :return: 
    """
    cluster_list = {}

    client = boto3.client('elasticache', region_name=region)
    clusters = client.describe_cache_clusters()
    i = 0
    for cluster in clusters["CacheClusters"]:
        arn = "arn:aws:elasticache:{0}:{1}:cluster:{2}".format(
            region,
            aws_arn_code,
            cluster["CacheClusterId"])
        tags = client.list_tags_for_resource(ResourceName=arn)
        cluster.update({"Tags": tags["TagList"]})
        total_matches = 0
        for tag in tags["TagList"]:
            kv = {"Name": tag["Key"], "Values": [tag["Value"]]}
            if kv in filters:
                total_matches += 1
                if len(filters) == total_matches:
                    cluster_list.update({i: [cluster, tags["TagList"]]})
                    i += 1
                    break
    return cluster_list


def cloudwatch_metrics(region, namespace="AWS/EC2",
                       metricname="CPUUtilization", dimensions=None,
                       starttime=None, endtime=None, period=300,
                       statistics=None):
    """

    :param region:
    :param namespace:
    :param metricname:
    :param dimensions:
    :param starttime:
    :param endtime:
    :param period:
    :param statistics:
    :return:
    """
    if statistics is None:
        statistics = ["Maximum", "Minimum", "Average"]

    session = boto3.session.Session(region_name=region)
    client = session.client('cloudwatch')

    return client.get_metric_statistics(
        Namespace=namespace,
        MetricName=metricname,
        Dimensions=dimensions,
        StartTime=starttime,
        EndTime=endtime,
        Period=period,
        Statistics=statistics)['Datapoints']


def find_elb(region, elb_id=None, instances=None):
    """

    :param region: 
    :param elb_id: 
    :param instances: 
    :return: 
    """
    client = boto3.client('elb', region_name=region)

    if elb_id is not None:
        elbs = client.describe_load_balancers(LoadBalancerNames=[elb_id])
        return elbs['LoadBalancerDescriptions']

    elif instances is not None:
        all_elbs = client.describe_load_balancers()
        elbs = []
        for instance in instances:
            for elb in all_elbs['LoadBalancerDescriptions']:
                if elb.get('Instances') is not None:
                    for instance_in_elb in elb['Instances']:
                        if instance_in_elb['InstanceId'] == instance:
                            elbs.append(elb)
        return elbs


def find_memcache(instance_id, region):
    """

    :param instance_id: 
    :param region: 
    :return: 
    """
    client = boto3.client('elasticache', region_name=region)
    instance = client.describe_cache_clusters(CacheClusterId=instance_id)

    return strip_metadata(instance)


def find_rds(instance_id, region, wait=False):
    """

    :param instance_id: 
    :param region: 
    :param wait: 
    :return: 
    """
    client = boto3.client('rds', region_name=region)

    if wait:
        waiter = client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=instance_id)

    instance = client.describe_db_instances(DBInstanceIdentifier=instance_id)
    return strip_metadata(instance)


def find_rds_snapshot(snapshot_id, region):
    """

    :param snapshot_id: 
    :param region: 
    :return: 
    """
    client = boto3.client('rds', region_name=region)
    instance = client.describe_db_snapshots(DBSnapshotIdentifier=snapshot_id)
    return strip_metadata(instance)


def create_rds_snapshot(instance_id, region):
    """

    CAUTION!! This will temporarily bring down RDS instance

    :param instance_id: 
    :param region: 
    :return: 
    """

    time_now = datetime.strftime(datetime.now(), '-%Y%m%d-%H%M')

    client = boto3.client('rds', region_name=region)
    snapshot_id = instance_id + time_now

    client.create_db_snapshot(
        DBSnapshotIdentifier=snapshot_id,
        DBInstanceIdentifier=instance_id)
    return snapshot_id


def latest_vpc_nat_image_id(region="us-west-1"):
    """

    :param region: 
    :return: 
    """
    ami = None
    client = boto3.client("ec2", region_name=region)
    images = client.describe_images(
        Owners=["amazon"],
        Filters=[
            {"Name": "name",
             "Values": ["*vpc-nat*"]},
            {"Name": "virtualization-type",
             "Values": ["hvm"]},
            {"Name": "root-device-type",
             "Values": ["ebs"]}])

    latest = ""
    for item in images["Images"]:
        if latest < item["CreationDate"]:
            latest = item["CreationDate"]
            ami = item["ImageId"]

    return ami


def describe_key_pairs(region="us-west-1"):
    """
    http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_key_pairs

    Get list of keypairs in a region
    :param region: AWS region string
    :return: 
    """
    client = boto3.client("ec2", region_name=region)
    images = client.describe_key_pairs()
    return images["KeyPairs"]


def describe_availability_zones(region="us-west-1"):
    """
    http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_availability_zones

    Get list of AZs of a region
    :param region: AWS region string
    :return: 
    """
    client = boto3.client("ec2", region_name=region)
    zones = client.describe_availability_zones()
    return zones["AvailabilityZones"]


def describe_vpcs(region="us-west-1"):
    """
    http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_vpcs

    Get list of VPCs in a region
    :param region: AWS region string
    :return:
    """
    client = boto3.client("ec2", region_name=region)
    vpcs = client.describe_vpcs()
    return vpcs["Vpcs"]


def describe_subnets(region="us-west-1", vpc_id=None):
    """
    http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_subnets

    Get a list of subnets for a VPC
    :param region: AWS region string
    :param vpc_id:
    :return:
    """
    client = boto3.client("ec2", region_name=region)
    subnets = client.describe_subnets(
        Filters=[
            {
                "Name": "vpc-id",
                "Values": [vpc_id]}])
    return subnets["Subnets"]


def strip_metadata(instance):
    """
    Strip the metadata from the response

    :param instance: 
    :return: dict of data from boto resources 
    """
    data = {}
    for itemlist in instance.keys():
        if itemlist == "ResponseMetadata":
            continue
        items = instance[itemlist][0]
        for key in items:
            data.update({key: items[key]})
    return data
