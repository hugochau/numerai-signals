"""
s3.py

Implements S3
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

import io

from module.logger.logger import Logger
from module.aws import Aws

logger = Logger().logger


class S3:
    """
    Purpose of this class is to implements
    various function to interact with a S3 bucket
    """

    def __init__(self, bucket: str, region: str = "eu-west-1"):
        """
        Class constructor

        :param bucket: bucket name
        :param region: bucket region

        ex: S3('bucket')
        """
        logger.info(f"Initializing {bucket}")
        self.bucket = bucket
        self.session = Aws.session()
        self.resource = self.session.resource("s3", region_name=region)

    def list_folder(self, folder_path: str) -> list:
        """
        List files within given folder

        ::param folderpath: absolute path to folder, considering bucket as root
        ::return folder content, returned as list
        """
        elements = self.resource.Bucket(self.bucket).objects.filter(Prefix=folder_path)
        return [element.key for element in elements]

    def upload_file(self, s3_file_path, local_file_path) -> dict:
        """
        Upload file at desired location

        ::param s3_file_path: absolute path to file, considering bucket as root
        ::param local_file_path: relative path to local file, starting at folder root

        ::return response: request response
        """
        logger.info(f"Uploading file {s3_file_path}")
        response = self.resource.Object(self.bucket, s3_file_path).put(
            Body=open(local_file_path, "rb")
        )

        return response

    def download_file(self, s3_file_path: str, local_file_path: str) -> None:
        """
        Download file from self.bucket

        ::param s3_file_path: where to find file in s3 bucket
        ::param local_file_path: where to save file
        """
        # download file
        response = self.resource.Bucket(self.bucket).Object(key=s3_file_path).get()

        # convert response into readable file and save
        io_bytes = io.BytesIO(response["Body"].read())
        io_text = io.TextIOWrapper(io_bytes, encoding="utf-8")
        with open(local_file_path, "w") as f:
            f.write(io_text.read())

    def delete_file(self, file_path) -> None:
        """
        Delete file from self.bucket

        ::param file_path: where to find file in s3 bucket
        """
        response = self.resource.Object(self.bucket, file_path).delete()

        if response["ResponseMetadata"]["HTTPStatusCode"] != 204:
            logger.info(response)
