"""
get_yahoo_tickers.py

Main script for loading raw data
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

import pandas as pd
import json
import warnings
import numerapi

warnings.filterwarnings("ignore")


def get_bloomberg_yahoo_mapping() -> pd.DataFrame:
    """
    Read in yahoo to bloomberg ticker map
    Add corrections

    ::return ticker_map mapping table
    """
    # read
    url = (
        "https://numerai-signals-public-data.s3-us-west-2.amazonaws.com/"
        "signals_ticker_map_w_bbg.csv"
    )

    # load bloomberg/yahoo mapping file
    ticker_map = pd.read_csv(url)

    # some corrections
    with open("data/config/ticker_corrections.json") as json_file:
        corrections = json.load(json_file)

    for old, new in corrections.items():
        # update if bloomberg_ticker already exists
        if old in ticker_map["bloomberg_ticker"].values:
            ticker_map.loc[ticker_map["bloomberg_ticker"] == old, "yahoo"] = new

        # append new row if not
        else:
            _row = {"ticker": old, "bloomberg_ticker": old, "yahoo": new}
            ticker_map = ticker_map.append(_row, ignore_index=True)

    return ticker_map


def get_numerai_tickers() -> list:
    """
    Get all the currently available tickers in our Numerai universe

    ::return: list of live tickers
    """
    napi = numerapi.SignalsAPI()

    return [x for x in napi.ticker_universe()]


def get_yahoo_tickers(ticker: str = None, ntickers: str = None) -> list:
    """
    This function helps mapping to yahoo tickers
    and to return the corresponding, cleaned list

    ::param ticker: optional ticker
    ::param ntickers: optional ticker list length
    ::return: list of live tickers
    """
    # get bloomberg/yahoo mapping
    ticker_map = get_bloomberg_yahoo_mapping()

    # get numerai live tickers
    universe = pd.Series(get_numerai_tickers())
    # avoids ValueError: Cannot merge a Series without a name
    universe.name = "universe"

    # join on universe.universe = ticker_map.bloomberg_ticker
    tickers = pd.merge(
        ticker_map,
        universe,
        how="inner",
        left_on="bloomberg_ticker",
        right_on="universe",
    )
    ticker_list = tickers.yahoo.dropna().to_list()

    # limit to first ntickers
    if ntickers:
        ticker_list = ticker_list[:ntickers]

    # limit to given ticker
    if ticker:
        try:
            ticker_list = [ticker_list[ticker_list.index(ticker)]]

        except ValueError as e:
            raise e

    return ticker_list
