import os
import boto3

from env import settings


class S3UploadFileObject(object):
    filename = None
    file = None

    def __init__(self, filename, file, mimetype) -> None:
        self.filename = filename
        self.file = file
        self.mimetype = mimetype


def getS3():
    """
    This function returns an S3 client object configured with AWS access keys and region settings from
    the provided settings file.
    :return: The function `getS3()` is returning an instance of the `boto3.client` class for Amazon S3,
    which is configured with the AWS access key ID, secret access key, and region specified in the
    `settings` module.
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )
    return s3_client


def upload_file(file, folder):
    """
    This function uploads a file to an AWS S3 bucket and returns the file's key and URL.

    :param file: The file parameter is the file object that needs to be uploaded to the S3 bucket
    :param folder: The folder parameter is a string that represents the name of the folder in which the
    file will be uploaded to in the AWS S3 bucket
    :return: a dictionary with two keys: "key" and "url".
    """
    s3_client = getS3()
    file_name = file.filename
    s3_key = os.path.join(folder, file_name)
    # save file to s3
    s3_client.upload_fileobj(
        file.file,
        settings.AWS_BUCKET_NAME,
        s3_key,
        ExtraArgs={'ContentType': f'{file.mimetype}; charset=utf-8'}
    )

    # set role read file
    s3_client.put_object_acl(
        Bucket=settings.AWS_BUCKET_NAME,
        Key=s3_key,
        ACL='public-read'
    )
    object_url = f"https://{settings.AWS_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
    return {
        "message": "Upload file success.",
        "success": True,
        "data": {
            "key": file_name,
            "url": object_url
        }
    }
