"""
test_yahoo.py

Implements Yahoo unit tests
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = 'numerai_2021@protonmail.com'

import os
import sys
import inspect
import datetime as dt

import pytest


currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(f'{parentdir}/src/numerai_signals')

from module.yahoo import Yahoo
# from module.exception import OperationalException
from util.get_tickers import get_yahoo_tickers


@pytest.mark.xfail(raises=AssertionError)
def test_yahoo_empty_request():
    """
    Expect OperationalException raised as empty request
    """
    crawler_start_date = dt.datetime.strptime('220301', '%y%m%d')
    crawler_start_date = crawler_start_date.replace(
        tzinfo=dt.timezone.utc
    ).timestamp()

    crawler_end_date = dt.datetime.strptime('220302', '%y%m%d')
    crawler_end_date = crawler_end_date.replace(
        tzinfo=dt.timezone.utc
    ).timestamp()

    tickers = get_yahoo_tickers()[:1]
    Yahoo(tickers, crawler_start_date, crawler_end_date).load_data()


def test_yahoo_valid_request():
    """
    Expect OperationalException raised as empty request
    """
    crawler_start_date = dt.datetime.strptime('220301', '%y%m%d')
    crawler_start_date = crawler_start_date.replace(
        tzinfo=dt.timezone.utc
    ).timestamp()

    crawler_end_date = dt.datetime.strptime('220303', '%y%m%d')
    crawler_end_date = crawler_end_date.replace(
        tzinfo=dt.timezone.utc
    ).timestamp()

    tickers = get_yahoo_tickers()[:1]
    df = Yahoo(tickers, crawler_start_date, crawler_end_date).load_data()

    assert not df.empty
