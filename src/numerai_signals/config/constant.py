"""
constant.py

Define globals here
"""

import logging
import datetime
import os


# data
DATA_FOLDER = 'data'

# logger
LOG_LEVEL = logging.INFO
LOG_FOLDER = os.path.join(DATA_FOLDER, 'log')
LOG_FILENAME = f'log_{datetime.datetime.isoformat(datetime.datetime.today())}'
LOG_FILEPATH = os.path.join(LOG_FOLDER, LOG_FILENAME)

# user agents for the yahoo finance API usage
USER_AGENTS = [
    (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko)'
        ' Chrome/39.0.2171.95 Safari/537.36'
    ),
    (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
        ' Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'
    )
]
