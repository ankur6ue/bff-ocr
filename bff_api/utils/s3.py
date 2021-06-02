import os
import boto3
import logging
import botocore
from .mysql import get_creds

def set_session_creds(app, role):

    # first try to read the creds from the mysql database
    credentials = get_creds(app.config["MYSQL"], role, app.logger)
    if credentials:
        os.environ['AWS_ACCESS_KEY_ID_SESS'] = credentials[1]
        os.environ['AWS_SECRET_ACCESS_KEY_SESS'] = credentials[2]
        os.environ['AWS_SESSION_TOKEN'] = credentials[3]
        return

    # Call the assume_role method of the STSConnection object and pass the role
    # ARN and a role session name. The ankur-dev profile must be available for this to work.. Which means
    # that the pod running this code can only be scheduled on the master node.
    session = boto3.Session(profile_name='ankur-dev')
    sts_client = session.client('sts')

    # print('aws_id: {0}'.format(aws_id) )
    # print('aws_secret: {0}'.format(aws_secret))
    assumed_role_object = sts_client.assume_role(
        RoleArn=role,
        RoleSessionName="S3AccessAssumeRoleSession",
        DurationSeconds=900  # valid for 15 min
    )


    # From the response that contains the assumed role, get the temporary
    # credentials that can be used to make subsequent API calls
    credentials = assumed_role_object['Credentials']
    os.environ['AWS_ACCESS_KEY_ID_SESS'] = credentials['AccessKeyId']
    os.environ['AWS_SECRET_ACCESS_KEY_SESS'] = credentials['SecretAccessKey']
    os.environ['AWS_SESSION_TOKEN'] = credentials['SessionToken']


def get_s3_client(logger):
    if not logger:
        logger = logging.getLogger(__name__)
    # Try reading from environment variable first. Otherwise try volume mounts
    aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY_SESS')
    if not aws_secret:
        with open('/etc/awstoken/AWS_SECRET_ACCESS_KEY_SESS') as file:
            aws_secret = file.read()

    aws_id = os.environ.get('AWS_ACCESS_KEY_ID_SESS')
    if not aws_id:
        with open('/etc/awstoken/AWS_ACCESS_KEY_ID_SESS') as file:
            aws_id = file.read()

    token = os.environ.get('AWS_SESSION_TOKEN')
    if not token:
        with open('/etc/awstoken/AWS_SESSION_TOKEN') as file:
            token = file.read()

    # logger.warning('aws_id = ' + aws_id)
    # logger.warning('token =' + token)
    # logger.warning('aws_secret = ' + aws_secret)

    s3_resource = boto3.resource(
        's3',
        aws_access_key_id=aws_id,
        aws_secret_access_key=aws_secret,
        aws_session_token=token
    )

    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_id,
        aws_secret_access_key=aws_secret,
        aws_session_token=token
    )
    return s3_client, s3_resource


def boto_response_ok(resp):
    return resp["ResponseMetadata"]["HTTPStatusCode"] == 200


def s3_to_local(bucket_name, prefix, extentions=['.jpg'], dest_base_path='/tmp', logger=None,
                s3_client=None, input_file_names=None):

    if not logger:
        logger = logging.getLogger(__name__)

    if input_file_names is None:
        logger.info('reading all image files from from S3 bucket {0}'.format(bucket_name))
    else:
        for file_name in input_file_names:
            logger.info('reading image {0} from from S3 bucket {1}'.format(file_name, bucket_name))

    # list objects
    try:
        if not s3_client:
            s3_client, _ = get_s3_client(logger=logger)

        files = []
        # Copy all image files from specified bucket/prefix to the destination directory and return local paths
        resp = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=1000)
        if boto_response_ok(resp):
            # create the dest_path if it doesn't exist
            os.makedirs(dest_base_path, exist_ok=True)
            for item in resp["Contents"]:
                # need os.path.split, because list_objects_v2 can return filenames with prefixes (eg. images/demo.jpg)
                # and we are only interested in demo.jpg
                _, filename = os.path.split(item['Key'])
                # if the user is interested in a specific file(s), ignore the rest
                if input_file_names is not None:
                    if filename not in input_file_names:
                        continue
                _, ext = os.path.splitext(filename)
                if ext in extentions:
                    dest_path = os.path.join(dest_base_path, filename)
                    s3_client.download_file(bucket_name, item['Key'], dest_path)
                    files.append(dest_path)
        return files
    except botocore.exceptions.ClientError as error:
        # Put your error handling logic here
        raise ValueError(error.args[0])


def upload_to_s3(local_file, bucket_name, file_name, logger=None):
    if not logger:
        logger = logging.getLogger(__name__)
    try:
        s3_client, _ = get_s3_client(logger)
        s3_client.upload_file(local_file, bucket_name, file_name)
    except botocore.exceptions.ClientError as error:
        # Put your error handling logic here
        raise ValueError(error.args[0])

# write_to_s3()
