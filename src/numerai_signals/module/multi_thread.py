"""
multi_thread.py

Implements MultiThread
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from module.logger.logger import Logger

logger = Logger().logger


class MultiThread:
    def __init__(self) -> None:
        self.processes = []

    def execute(self, tasks, function, params=None):
        with ThreadPoolExecutor(max_workers=100) as executor:
            for task in tasks:
                # send jobs to pool
                logger.info(f"Executing {task}")
                # proc_params = {"task": task, "params": params, "count": tasks.index(task)}
                proc_params = {"task": task, "params": params}
                self.processes.append(executor.submit(function, proc_params))

    def parse_yahoo(self):
        df = pd.DataFrame()

        # parse responses into tuple and append to final frame
        for task in as_completed(self.processes):
            response = task.result()
            try:
                # indicators
                # open, high, low, close, volume
                quote = response["chart"]["result"][0]["indicators"]["quote"][0]
                # creating frame from this indicator dict
                df_tmp = pd.DataFrame.from_dict(quote)

                # adding metadata
                # ticker
                df_tmp["ticker"] = response["chart"]["result"][0]["meta"]["symbol"]

                # timestamp
                # we combine utc timestamp with gmtoffset
                # in order to get local timestamp
                # this avoids getting timestamp outside of [start, end[
                # in particular for those ticker in gmt+X timezones
                utc_timestamp = response["chart"]["result"][0]["timestamp"]
                gmt_offset = response["chart"]["result"][0]["meta"]["gmtoffset"]
                local_timestamp = []
                for ts in utc_timestamp:
                    local_timestamp.append(ts + gmt_offset)

                df_tmp["timestamp"] = local_timestamp
                df_tmp["timestamp"] = pd.to_datetime(df_tmp["timestamp"], unit="s")

                # currency
                df_tmp["currency"] = response["chart"]["result"][0]["meta"]["currency"]

                # limit to one result per day = stock opening time
                # its is not clear what the other entries are meant for
                df_tmp.sort_values(by=["timestamp"])
                df_tmp["date"] = df_tmp.timestamp.dt.date
                df_tmp.drop_duplicates(subset=["date"], inplace=True)
                df_tmp.drop(columns=["date"], inplace=True)

                df = df.append(df_tmp)

            except Exception as e:
                # pass if could not parse response
                logger.info(f"Exception: {e}")
                pass

        return df

    def parse_transform(self):
        df = pd.DataFrame()

        # parse responses into tuple and append to final frame
        for task in as_completed(self.processes):
            response = task.result()
            try:
                df = df.append(response)

            except Exception as e:
                # pass if could not parse response
                logger.info(f"Exception: {e}")
                pass

        return df

    def parse_square(self):
        res = []
        # parse responses into tuple and append to final frame
        for task in as_completed(self.processes):
            response = task.result()
            try:
                res.append(response)

            except Exception as e:
                # pass if could not parse response
                logger.info(f"Exception: {e}")
                pass

        return sorted(res)

    def parse_upload(self):
        res = 0
        # parse responses into tuple and append to final frame
        for task in as_completed(self.processes):
            response = task.result()
            try:
                if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                    res += 1

            except Exception as e:
                # pass if could not parse response
                logger.info(f"Exception: {e}")
                pass

        return res
