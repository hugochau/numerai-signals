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

from module.multi_thread import MultiThread

mt = MultiThread()

def square(params):
    return params['task']*params['task']

def test_execute():
    tasks = [i for i in range(100)]

    mt.execute(tasks, square)

    assert len(mt.processes) > 0

def test_parse():
    res = mt.parse_square()

    print(res)

    assert len(res) > 0
    assert res[0] == 0
