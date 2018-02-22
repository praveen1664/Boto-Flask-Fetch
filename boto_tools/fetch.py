import boto_queries


class ValidationError(Exception):
    pass


def aws_regions():
    """
    boto3 query for all aws regions
    :return: list of region strings 
    """
    regions = boto_queries.describe_regions()
    region_names = []
    for region in regions:
        region_names.append(region["RegionName"])
    return region_names


def fetch(state=None, region=None, tags=None,
          unique_ids=None, single_region=None):
    """

    :param state: 
    :param region: 
    :param tags: 
    :param unique_ids:
    :param single_region: 
    :return: 
    """
    if not tags and not unique_ids:
        raise ValidationError("search tags required")
    else:
        tags = tags if tags else []
        unique_ids = unique_ids if unique_ids else {}

    tag_filters = []
    try:
        if not region:
            regions = aws_regions()
        else:
            regions = [region]

        single_region = single_region == "1"

        for tag in tags:
            tag_filters.append({"Name": tag[0], "Values": [tag[1]]})

        if state:
            acceptable_states = ["running", "pending", "stopping",
                                 "stopped", "terminated"]
            if state not in acceptable_states:
                raise ValidationError("`state` can only one of " +
                                      ", ".join(acceptable_states))
    except Exception as e:
        raise ValidationError(str(e))

    instances = []
    for region in regions:
        try:
            region_instances = tag_query(tags=tag_filters,
                                         region=region,
                                         state=state,
                                         unique_ids=unique_ids)
        except Exception:
            raise
        instances += region_instances
        if single_region and len(instances) > 0:
            break
    return instances


def tag_query(tags=None, region=None, state=None, unique_ids=None):
    """

    :param tags: list (aws filter formatted list)
    :param region: string
    :param state: string 
    :return: JSON List of instance objects
    """
    if not region:
        raise ValidationError("region required for instance lookup")
    elif not tags and not unique_ids:
        raise ValidationError("tags or ids required for instance lookup")

    filters = []
    if unique_ids:
        # these ids *usually* describe a single instance
        if "id" in unique_ids.keys():
            filters = [{"Name": "instance-id",
                        "Values": [unique_ids["id"]]}]
        elif "public-ip" in unique_ids.keys():
            filters = [{"Name": "ip-address",
                        "Values": [unique_ids["public-ip"]]}]
        elif "private-ip" in unique_ids.keys():
            filters = [{"Name": "private-ip-address",
                        "Values": [unique_ids["private-ip"]]}]

    if tags:
        filters += tags

    # Add-on to filters
    if state:
        filters.append({'Name': 'instance-state-name', 'Values': [state]})
    print filters
    # Start the search for instances matching the filters
    reservations = boto_queries.ec2_client(filters, region)
    raw = []
    for r in reservations:
        for instance in r['Instances']:
            raw.append(instance)
    return raw  # is a list of instances
