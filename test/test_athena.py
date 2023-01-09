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

from module.athena import Athena
from module.app import App

def test_succeeded_run_query():
    App.set('aws_account_id', '615955932111')

    with open('src/numerai_signals/sql/data_dummy.sql', 'r') as f:
        sql_script = f.read()

    query_result = Athena().run_query(sql_script)[0]

    assert query_result == 'SUCCEEDED'
