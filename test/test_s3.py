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

from module.aws.s3 import S3


@pytest.fixture
def s3_resource():
    return S3('615955932111-test')

def test_download_file_from_s3(s3_resource):
    s3_resource.download_file('hello.txt', 'data/hello.txt')

def test_delete_file(s3_resource):
    s3_resource.delete_file('hello.txt')

def test_upload_file(s3_resource):
    s3_resource.upload_file('hello.txt', 'data/hello.txt')

# def test_delete_file_not_exists():
#     assert s3.delete_file('hugo.txt')

# def test_list_folder():
#     response = s3.list_folder('transform/')

#     print(response)
#     assert True
