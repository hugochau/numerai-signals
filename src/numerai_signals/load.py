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
from module.aws import Aws
from module.s3 import S3
from util.get_tickers import get_yahoo_tickers
from util.parse_args import parse_args_load
from util.optimise_frame import optimise_frame


def upload(params):
    df = params["params"]["df"]
    day = params["task"]
    s3 = params["params"]["s3"]

    tmp = df[df["timestamp"] == day]
    day_datetime = pd.to_datetime(day)
    day_str = day_datetime.strftime("%y%m%d%H%M%S")
    filename = f"yahoo_data_{day_str}"

    # datalake folder partition
    _year = day_datetime.year
    _month = day_datetime.month
    _day = day_datetime.day

    # save file
    tmp.to_parquet(f"data/raw_data/{filename}.parquet", index=False)
    # tmp.to_csv(f"data/raw_data/{filename}.csv", index=False)

    # upload file to s3
    source_path = f"data/raw_data/{filename}.parquet"
    target_folder = f"raw_data/yahoo/{_year}/{_month}/{_day}"
    target_path = f"{target_folder}/{filename}.parquet"

    response = s3.upload_file(target_path, source_path)

    # remove local file
    os.remove(f"data/raw_data/{filename}.parquet")

    return response


def delete(params):
    s3 = params["params"]["s3"]
    logger = Logger().logger

    # datalake folder partition
    _date = pd.to_datetime(params["task"])
    _year = _date.year
    _month = _date.month
    _day = _date.day

    # delete file from s3
    target_folder = f"raw_data/yahoo/{_year}/{_month}/{_day}"

    files = s3.list_folder(target_folder)
    for file in files:
        logger.info(f"Deleting {file}")
        s3.delete_file(file)

    files = s3.list_folder(target_folder)
    if files:
        logger.info(
            f'{OperationalException("Empty folder operation failed. Exiting.")}'
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

        # define crawler boundaries
        crawler_start_date = dt.datetime.strptime(args.start, "%y%m%d")
        crawler_end_date = dt.datetime.strptime(args.end, "%y%m%d")
        logger.info(
            f'Crawler date range: {crawler_start_date.strftime("%y%m%d")} '
            f'{crawler_end_date.strftime("%y%m%d")}'
        )

        # download tickers them from numerai
        logger.info(f"Collecting tickers")
        tickers = get_yahoo_tickers(args.ticker, args.ntickers)
        logger.info(f"Crawler coverage: {len(tickers)} tickers")

        # run yahoo finance API crawler
        df = Yahoo(tickers, crawler_start_date, crawler_end_date).load_data()

        # optimize frame
        df = optimise_frame(df)

        # split by day to enable file overwritting
        days = df.sort_values(by=["timestamp"]).timestamp.unique()

        # get aws acount_id and initialize s3 resource
        aws_account_id = Aws().get_account_id()
        s3 = S3(f"{aws_account_id}-signals-data")

        # call multi thread to empty partition folders
        mtd = MultiThread()
        mtd.execute(days, delete, {"s3": s3})

        # call multi thread to upload files
        mtu = MultiThread()
        mtu.execute(days, upload, {"df": df, "s3": s3})
        logger.info(f"Nfiles uploaded: {mtu.parse_upload()}")

        _time = round(time() - run_start_time, 2)
        logger.info(f"Time taken: {round(_time/60, 2)}min ({_time}sec)")
        logger.info("🔥")

    except Exception as e:
        logger.error(e, exc_info=True)


if __name__ == "__main__":
    main()
