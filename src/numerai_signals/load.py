"""
load.py

Main script for loading raw data
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

import datetime as dt
from time import time
import os

import pandas as pd

from module.logger.logger import Logger
from module.yahoo import Yahoo
from module.app import App
from module.multi_thread import MultiThread
from module.exception import OperationalException
from module.aws.aws import Aws
from module.aws.s3 import S3
from util.get_tickers import get_yahoo_tickers
from util.parse_args import parse_args_load
from util.optimise_frame import optimise_frame


def upload(params: dict) -> dict:
    """
    Upload data to signals-data for a given day - partition.

    ::param params:
        - task: day
        - params
            - df: data to upload
            - s3: bucket to upload to

    ::return response: s3.upload_file response
    """
    logger = Logger().logger

    # parse parameters dict
    df = params["params"]["df"]  # original df
    day = params["task"]  # day to filter df with
    s3 = params["params"]["s3"]  # target s3

    # filtering df on given day
    # because we want to upload to target partition folder
    # only that portion of the data
    tmp = df[df["timestamp"] == day]

    day_datetime = pd.to_datetime(day)
    day_str = day_datetime.strftime("%y%m%d")

    # filename format yahoo_data_YYMMDD
    filename = f"yahoo_data_{day_str}"

    # saving file locally first
    source_path = f"data/raw_data/{filename}.parquet"
    tmp.to_parquet(source_path, index=False)

    # we determine bucket folder using day_datetime
    _year = day_datetime.year
    _month = day_datetime.month
    _day = day_datetime.day
    target_folder = f"raw_data/yahoo/{_year}/{_month}/{_day}"
    target_path = f"{target_folder}/{filename}.parquet"

    # upload it to s3 target folder
    logger.info(f"{tmp.shape[0]} entries to upload to {target_path}")
    response = s3.upload_file(target_path, source_path)

    # remove local file
    os.remove(source_path)

    return response


def delete(params) -> None:
    """
    Delete old data from signals-data before uploading new data

    ::param params:
        - task: day
        - params
            - s3: bucket to upload to
    """
    logger = Logger().logger

    # parse parameters dict
    day = params["task"]
    s3 = params["params"]["s3"]

    # we determine bucket folder using day_datetime
    _date = pd.to_datetime(day)
    _year = _date.year
    _month = _date.month
    _day = _date.day
    target_folder = f"raw_data/yahoo/{_year}/{_month}/{_day}"

    # delete/empty file from s3
    logger.info(f"Emptying {target_folder}")
    files = s3.list_folder(target_folder)
    for file in files:
        s3.delete_file(file)

    # checking if folder is actually empty
    # raise OperationalException if not. this prevents from double inserting
    files = s3.list_folder(target_folder)
    if files:
        logger.error(
            f'{OperationalException("Empty folder operation failed. Exiting.")}',
            exc_info=True,
        )


def main():
    """
    Main script for loading raw data
    """
    run_start_time = time()
    logger = Logger().logger
    logger.info(f"Begin")

    try:
        # parse args
        args = parse_args_load()

        # set environment context
        App.set("local", args.local)

        # convert crawler boundaries, args.start and args.end
        # to datetime first
        start_date = dt.datetime.strptime(args.start, "%y%m%d")
        end_date = dt.datetime.strptime(args.end, "%y%m%d")
        logger.info(
            f'Crawler date range: [{start_date.strftime("%y%m%d")}, '
            f'{end_date.strftime("%y%m%d")}['
        )
        # then to timestamp
        # somehow tzinfo is not utc so we replace it first
        # and then convert to timestamp
        start_ts = start_date.replace(tzinfo=dt.timezone.utc).timestamp()
        end_ts = end_date.replace(tzinfo=dt.timezone.utc).timestamp()

        # download tickers list from numerai
        logger.info(f"Collecting tickers")
        tickers = get_yahoo_tickers(args.ticker, args.ntickers)
        logger.info(f"Crawler coverage: {len(tickers)} tickers")

        # run yahoo finance API crawler
        logger.info(f"Crawling API")
        df = Yahoo(tickers, start_ts, end_ts).load_data()

        # limit curled data to [start_date, end_date[
        # it is not clear why the API returns data outside of boundaries
        df = df[(df["timestamp"] >= start_date) & (df["timestamp"] < end_date)]

        # optimize frame
        df = optimise_frame(df)

        # get aws acount_id and initialize s3 resource
        aws_account_id = Aws().get_account_id()
        s3 = S3(f"{aws_account_id}-signals-data")

        # call multi thread to empty partition folders
        mtd = MultiThread()
        days = df.timestamp.unique()
        # one process per bucket partition to empty
        mtd.execute(days, delete, {"s3": s3})

        # call multi thread to upload files
        mtu = MultiThread()
        days = df.timestamp.unique()
        # one process per day (bucket partition) to upload
        mtu.execute(days, upload, {"df": df, "s3": s3})
        logger.info(f"Nfiles uploaded: {mtu.parse_upload()}")

        # logging run time
        _time = round(time() - run_start_time, 2)
        logger.info(f"Time taken: {round(_time/60, 2)}min ({_time}sec)")
        logger.info("🔥")

    # log traceback on error
    except Exception as e:
        logger.error(e, exc_info=True)


if __name__ == "__main__":
    main()
