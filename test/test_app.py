"""
test_app.py

Implements App unit tests
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

from module.app import App

def test_app_setter_valid():
    App.set('today', 'today')

    assert App.config('today') == 'today'


@pytest.mark.xfail(raises=NameError)
def test_app_setter_invalid():
    App.set('test', 'today')
