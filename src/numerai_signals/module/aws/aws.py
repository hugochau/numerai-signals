"""
aws.py

Implements Aws
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

import boto3

from module.app import App
from module.logger.logger import Logger

from util.get_aws_creds import get_aws_creds

logger = Logger().logger


class Aws:
    """
    Purpose of this class is to implement
    various function to interact with a S3 bucket
    """

    def __init__(self) -> None:
        self.session = Aws.session()

    @staticmethod
    def session() -> boto3.session.Session:
        """
        Initializes boto3 Session object. Using:
            - credential file if running inside local container
            - naws solution - roles - if running inside ecs container

        ::return boto3.session.Session object
        """
        # credential solution
        if App.config("local"):
            logger.info("Initializing AWS Session object, credential solution")
            creds = get_aws_creds()

            return boto3.session.Session(
                aws_access_key_id=creds["access_key_id"],
                aws_secret_access_key=creds["secret_access_key"],
            )

        # native aws solution
        else:
            logger.info("Initializing AWS Session object, naws solution")
            # self.session=boto3.session.Session(profile_name='jh_numerai')
            return boto3.session.Session()

    # @staticmethod
    # def client(service: str) -> boto3.client:
    #     """
    #     Initializes boto3 client object. Using:
    #         - credential file if running inside local container
    #         - naws solution - roles - if running inside ecs container

    #     ::param service: AWS service
    #         ex: sts

    #     ::return boto3.client object
    #     """
    #     if App.config("local"):
    #         return boto3.client(
    #             service,
    #             aws_access_key_id=creds["access_key_id"],
    #             aws_secret_access_key=creds["secret_access_key"],
    #         )

    #     else:
    #         boto3.client(service)

    def get_account_id(self):
        """
        Retrieve AWS account ID

        ::return
        """

        return self.session.client("sts").get_caller_identity()["Account"]
