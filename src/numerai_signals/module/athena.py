"""
athena.py

Implements Athena
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

from module.logger.logger import Logger
from module.app import App
from module.aws import Aws

logger = Logger().logger


class Athena:
    """
    Purpose of this class is to implements
    various function to interact with AWS Athena
    """

    def __init__(self, region: str = "eu-west-1"):
        """
        Class constructor
        """
        self.session = Aws.session()
        self.client = self.session.client(service_name="athena", region_name=region)

    def run_query(self, query: str, database: str = "signals") -> tuple:
        """
        Run query against given database

        ::param query: query to execute
        ::param database: database to query

        ::return (query_status, query_id)
            - query_status: request status code. 200 if success
            - query_id: request id
        """
        # start query
        output_folder = f"s3://{App.config('aws_account_id')}-athena"
        response_execution_start = self.client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={"Database": database},
            ResultConfiguration={"OutputLocation": output_folder},
        )

        # get query id
        query_id = response_execution_start["QueryExecutionId"]

        # get query execution status
        response_execution = self.client.get_query_execution(QueryExecutionId=query_id)

        # if HTTP request is successfull, keep updating query_status until
        # it falls in ('SUCCEEDED', 'FAILED', 'CANCELLED')
        if response_execution_start["ResponseMetadata"]["HTTPStatusCode"] == 200:
            logger.info(f"Query id {query_id} is running")
            query_status = "RUNNING"

            # get latest query execution status
            # and update query_status accordingly
            # loop until expected value
            while query_status not in ("SUCCEEDED", "FAILED", "CANCELLED"):
                logger.info(f"Query is {query_status}")
                response_execution = self.client.get_query_execution(
                    QueryExecutionId=response_execution_start["QueryExecutionId"]
                )

                query_status = response_execution["QueryExecution"]["Status"]["State"]

        logger.info(f"Query {query_status}")
        return (query_status, response_execution_start["QueryExecutionId"])
