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
    Purpose of this class is to curl yahoo finance API
    and parse result into proper dataframe
    """

    def __init__(self, tickers: list, start: str, end: str):
        """
        Class constructor

        ::param tickers: list of tickers to crawl
        ::param start: crawler start date
        ::param end: crawler end date

        ex: Yahoo('AMZN', '221001', '221002')
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
        params = dict(
            period1=int(self.start.timestamp()),
            period2=int(self.end.timestamp()),
            interval="1d",
            events="div,splits",
        )

        # call multi thread to curl urls
        mt = MultiThread()
        mt.execute(urls, curl_url, params)
        df = mt.parse_yahoo()

        # raise exception if resulting df is empty
        try:
            assert not df.empty

        except AssertionError as e:
            raise e

        return df
