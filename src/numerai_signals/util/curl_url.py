"""
curl_url.py

Define custom exceptions
"""

import requests
import random

from config.constant import USER_AGENTS
from module.logger.logger import Logger

logger = Logger().logger


def curl_url(params: dict) -> dict:
    """
    Basic funtion to request data from the API

    ::param url: crawled URL
    ::param: params: request parameters

    ::return response data
    """
    try:
        data = requests.get(
            url=params["task"],
            params=params["params"],
            headers={"User-Agent": random.choice(USER_AGENTS)},
        )

        return data.json()

    except Exception as e:
        # pass if could not parse response
        logger.info(f"Exception: {e}")
        pass
