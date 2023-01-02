"""
test_s3.py

Implements S3 unit tests
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

from util.parse_args import validate_load_args

# @pytest.fixture(scope='session')
# def start(pytestconfig):
#     return pytestconfig.getoption('start')

# @pytest.fixture(scope='session')
# def end(pytestconfig):
#     return pytestconfig.getoption('end')

# @pytest.fixture(scope='session')
# def ticker(pytestconfig):
#     return pytestconfig.getoption('ticker')


@pytest.mark.xfail(raises=AssertionError)
def test_validate_negative_ntickers():
    validate_load_args(ntickers=-1)


@pytest.mark.xfail(raises=ValueError)
def test_validate_wrong_date_format():
    validate_load_args(start='220103', end='2201034')


@pytest.mark.xfail(raises=AssertionError)
def test_validate_date_order():
    validate_load_args(start='220103', end='220103')
