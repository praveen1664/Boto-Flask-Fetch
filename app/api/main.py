from flask import jsonify, request
from app import app
from boto_tools import fetch


def get_url_args():
    data = {}
    try:
        for key in request.values:
            data.update({key: request.values[key]})
    except Exception as e:
        print str(e)
    return data


@app.route("/api/fetch-regions", methods=["GET"])
def api_fetch_regions():
    """

    :return: JSON data 
    """
    try:
        response_data = fetch.aws_regions()
    except fetch.ValidationError as e:
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

    return jsonify({"data": response_data})


@app.route("/api/fetch", methods=["GET"])
def api_fetch():
    """
    
    :return: JSON data 
    """
    args = get_url_args()
    instance_id = args.get("id")
    public_ip = args.get("public-ip")
    private_ip = args.get("private-ip")
    region = args.get("region")
    single_region = args.get("single-region")
    state = args.get("state")

    tags = []
    for key, value in args.iteritems():
        if "tag:" not in key:
            continue
        tags.append((key, value))

    unique_ids = {}
    if args.get("id"):
        unique_ids.update({"id": instance_id})

    elif args.get("public-ip"):
        unique_ids.update({"public-ip": public_ip})

    elif args.get("private-ip"):
        # semi unique id, depending on your infrastructure
        unique_ids.update({"private-ip": private_ip})

    try:
        response_data = fetch.fetch(tags=tags,
                                    region=region,
                                    state=state,
                                    unique_ids=unique_ids,
                                    single_region=single_region,
                                    )
    except fetch.ValidationError as e:
        return jsonify({"msg": str(e)}), 400
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

    return jsonify({"data": response_data})
