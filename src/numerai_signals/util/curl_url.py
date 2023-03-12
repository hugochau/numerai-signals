"""
curl_url.py

Define curl_url
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

import requests
import random

from config.constant import USER_AGENTS
from module.logger.logger import Logger

logger = Logger().logger


def curl_url(params: dict) -> dict:
    """
    Curl URL

    ::param: params
        - task: url, requested URL
        - params: request parameters
            period1 lower boundary, inclusive
            period2 upper boundary, inclusive
            interval=1d
            events=history

    ::return response data
    """
    url = params["task"]
    try:
        logger.info(f"Crawling {url}")
        data = requests.get(
            url=url,
            params=params["params"],
            headers={"User-Agent": random.choice(USER_AGENTS)},
        )

        return [url, data.json()]

    except Exception as e:
        # return none if exception
        logger.info(f"Exception {url}: {e}")
        return [url, None]
