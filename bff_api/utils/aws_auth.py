import os
import boto3
import botocore.exceptions


def read_env_var(env_file_list, destination):
    # Reads environment variables from provided file list and adds them to the destination dictionary
    for file in env_file_list:
        if os.path.isfile(file):
            with open(file) as f:
                for line in f:
                    name, var = line.partition("=")[::2]
                    destination[name] = var.rstrip()


class AWSAuth:
    def __init__(self):
        pass

    def create_presigned_post(self, region_name, bucket_name, object_name, fields=None,
                              conditions=None, expiration=100):
        # Generate a presigned S3 POST URL
        ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID_SESS")
        SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY_SESS")
        SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN")

        try:
            s3_client = boto3.client("s3",
                                     region_name=region_name,
                                     aws_access_key_id=ACCESS_KEY,
                                     aws_secret_access_key=SECRET_KEY,
                                     aws_session_token=SESSION_TOKEN)

            response = s3_client.generate_presigned_post(Bucket=bucket_name,
                                                         Key=object_name,
                                                         Fields=fields,
                                                         Conditions=conditions,
                                                         ExpiresIn=expiration)
            return response
        except botocore.exceptions.ClientError as error:
            # Put your error handling logic here
            raise ValueError('The parameters you provided are incorrect: {}'.format(error))

        except botocore.exceptions.ParamValidationError as error:
            raise ValueError('The parameters you provided are incorrect: {}'.format(error))

        except TypeError as e:
            raise ValueError('TypeError: {}'.format(e))

        except Exception as e:
            raise ValueError('The parameters you provided are incorrect: {}'.format(e.fmt))
