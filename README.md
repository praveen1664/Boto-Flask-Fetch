# Boto-Flask-Fetch
Search your AWS infrastructure with Boto3 wrapped inside a Flask api
# Boto3 Flask FetchSearch your AWS infrastructure with Boto3 wrapped inside a Flask api.
**Setup**
```virtualenv venvvenv/bin/pip install -r requirements.txt```
**Run**
```venv/bin/python run.py```
**Use**
Try running 
``` curl localhost:6000/api/fetch-regions```
to get the following response
```{  "data": [    "ap-south-1",    "eu-west-2",    "eu-west-1",    "ap-northeast-2",    "ap-northeast-1",    "sa-east-1",    "ca-central-1",    "ap-southeast-1",    "ap-southeast-2",    "eu-central-1",    "us-east-1",    "us-east-2",    "us-west-1",    "us-west-2"  ]}```
## Fetch API
Example: fetch ec2-instance with tags
```curl "localhost:6000/api/fetch?tag:Environment=dev&state=running"```
**URL Params**-
*Search Criteria*
- **state** - aws instance state- **region** - aws-region- **id** - aws instance id- **public-ip** - public ip address of ec2-instance- **private-ip** - private ip address of ec2-instance- **tag:*** - any tag name to match
 Tag Examples:  - tag:Name=srvX - tag:Environment=dev
*Functions* 
- **single-region** - [0 or 1] - if a region is not specified and single-region=1, returns the first instance(s) matching search criteria within a region loop
