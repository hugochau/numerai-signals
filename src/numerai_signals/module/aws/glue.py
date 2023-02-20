"""
glue.py

Implements Glue
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"


import threading

from module.logger.logger import Logger
from module.exception import OperationalException
from module.app import App
from module.aws.aws import Aws

logger = Logger().logger


class Glue:
    """
    A class to implement methods to interact with AWS Glue service.
    """

    def __init__(self, region: str = "eu-west-1"):
        """
        Class constructor
        """
        self.session = Aws.session()
        self.client = self.session.client(service_name="glue", region_name=region)

    def run_crawler(self, name: str) -> None:
        """
        Run crawler and wait until - successfull or not - completion

        ::param name: crawler name

        ::return (query_status, query_id)
            - query_status: request status code. 200 if success
            - query_id: request id
        """
        if self.get_crawler_state(name) == 'READY':
            # start crawler
            self.client.start_crawler(Name=name)

            # get query execution status
            crawler_state = self.get_crawler_state(name)

            # if crawler is running
            # keep updating crawler_state until it is 'READY' again
            if crawler_state == 'RUNNING':
                logger.info(f"Crawler {name} is running")

                # get latest crawler_state
                # update crawler_state accordingly
                # loop until expected value
                while crawler_state != "READY":
                    logger.info(f"Crawler is {crawler_state}")
                    crawler_state = self.get_crawler_state(name)
                    threading.Event().wait(3)

            logger.info(f"Crawler completed")
            crawler_result = self.get_crawler_result(name)

            logger.info(crawler_result)

        else:
            raise OperationalException("Reload operation failed. Exiting.")


    def get_crawler_state(self, name: str) -> str:
        """
        Get crawler current state

        ::param name: crawler name

        ::return state
        """
        response = self.client.get_crawler(Name=name)
        state = response["Crawler"]["State"]

        return state

    def get_crawler_result(self, name: str) -> str:
        """
        Get crawler last run result

        ::param name: crawler name

        ::return state
        """
        response = self.client.get_crawler(Name=name)

        return response["Crawler"]["LastCrawl"]