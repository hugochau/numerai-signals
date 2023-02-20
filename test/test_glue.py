"""
test_s3.py

Implements S3 unit tests
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = 'numerai_2021@protonmail.com'

import os
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.append(f'{parentdir}/src/numerai_signals')

from module.aws.glue import Glue
from module.app import App

App.set('aws_account_id', '615955932111')

def test_get_crawler_state():

    state = Glue().get_crawler_state('615955932111-signals-crawler')

    assert state == 'READY'

def test_get_crawler_result():
    result = Glue().get_crawler_result('615955932111-signals-crawler')

    assert result['LogGroup'] == '/aws-glue/crawlers'
