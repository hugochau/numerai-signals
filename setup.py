"""
setup.py

Setup python entry points, test folder, etc.
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = 'numerai_2021@protonmail.com'

from setuptools import find_packages
from setuptools import setup


with open('requirements.txt') as f:
    content = f.readlines()
requirements = [x.strip() for x in content if 'git+' not in x]

setup(name='numerai_signals',
      version="1.0",
      description="Project Description",
      packages=find_packages(),
      install_requires=requirements,
      test_suite='test',
      # include_package_data: to install data from MANIFEST.in
      include_package_data=True)
    #   scripts=['scripts/numerai_signals-run'],
    #   zip_safe=False)
