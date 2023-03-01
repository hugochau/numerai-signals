"""
yahoo.py

Implements Yahoo
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

import pandas as pd

from module.logger.logger import Logger
from module.multi_thread import MultiThread
from util.curl_url import curl_url

logger = Logger().logger


class Yahoo:
    """
    Purpose of this class:
        - curl yahoo finance API
        - parse result in dataframe
    """

    def __init__(self, tickers: list, start: str, end: str):
        """
        Class constructor

        ::param tickers: list of tickers to crawl
        ::param start: crawler start date, unix UTC timestamp
        ::param end: crawler end date, unix UTC timestamp

        ex: Yahoo('AMZN', 'XXXXX', 'YYYYY')
        """
        self.tickers = tickers
        self.start = start
        self.end = end

    def load_data(self) -> pd.DataFrame:
        """
        Curl yahoo finance API for given ticker list
        Parse response into tuple and append to output frame

        ::return df: output frame
        """
        # build request urls
        api_url = "https://query2.finance.yahoo.com/v8/finance/chart"
        urls = [f"{api_url}/{ticker}" for ticker in self.tickers]

        # define request parameters
        # period2 is inclusive so we put -1 to exclude upper boundary
        # [start, end - 1] = [start, end[
        params = dict(
            period1=int(self.start),
            period2=int(self.end) - 1,
            interval="1d",
            # events="div,splits",
            events="history",
        )

        # call multi thread to curl urls
        mt = MultiThread()
        # one process per URL - ticker - to curl
        mt.execute(urls, curl_url, params)
        df = mt.parse_yahoo()

        # raise exception if resulting df is empty
        try:
            assert not df.empty

        except AssertionError as e:
            raise e

        return df
