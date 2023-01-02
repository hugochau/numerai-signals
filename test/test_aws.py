"""
test_s3.py

Implements S3 unit tests
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = 'numerai_2021@protonmail.com'

import os
import sys
import logging
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(f'{parentdir}/src/numerai_signals')

from module.aws import Aws
from module.app import App
from module.logger.logger import Logger

logger = Logger().logger


# def test_credential_session(caplog):
#     with caplog.at_level(logging.INFO):
#         App.set('local', True)
#         aws = Aws()

#     assert 'credential solution' in caplog.text
#     # assert True


def test_get_account_id():
    """
    Must set AWS_PROFILE=numerai_dev beforehand!
    """
    assert Aws().get_account_id() == '615955932111'
