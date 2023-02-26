"""
test_get_yahoo_tickers.py

Implements get_yahoo_tickers unit tests
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = 'numerai_2021@protonmail.com'

import os
import sys
import inspect

import pytest

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(f'{parentdir}/src/numerai_signals')

from util.get_tickers import get_yahoo_tickers


def test_get_yahoo_tickers_ticker():
    assert get_yahoo_tickers(ticker='AAPL') == ['AAPL']


def test_get_yahoo_tickers_nticker():
    assert len(get_yahoo_tickers(ntickers=10)) == 10


@pytest.mark.xfail(raises=ValueError)
def test_get_yahoo_tickers_not_exists():
    get_yahoo_tickers(ticker='Hugo')
