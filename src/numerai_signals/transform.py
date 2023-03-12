"""
transform.py

Main script for transforming raw data
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

from time import time
import datetime

import pandas as pd
import numpy as np

from module.logger.logger import Logger
from module.exception import OperationalException
from module.multi_thread import MultiThread
from module.aws.aws import Aws
from module.aws.s3 import S3
from module.aws.athena import Athena
from module.aws.glue import Glue
from module.app import App
from module.transformer import Transformer
from util.parse_args import parse_args_transform
from util.optimise_frame import optimise_frame


def transform(params):
    logger = Logger().logger
    df = params["params"]["df"]
    cmd = params["params"]["cmd"]
    ticker = params["task"]

    try:
        trans = Transformer()

        # Create a final frame with the transformed tickers
        df_ticker = df[df["ticker"] == ticker]
        # derniere date=aujourd'hui=derniere ligne
        df_ticker.sort_values(by=["timestamp"], inplace=True)

        # This is where the magic happens
        logger.info(f"processing {ticker}")
        df_ticker = getattr(trans, f"{cmd}_indicators")(df_ticker)

        for i in df_ticker.columns[3:]:
            df_ticker = trans.shifter(df_ticker, i)

        df_ticker = optimise_frame(df_ticker)
        df_ticker = df_ticker[df_ticker["timestamp"].dt.weekday == 4]
        logger.info(f"processed {ticker}")

        return df_ticker

    except BaseException as e:
        logger.error(f"Error while processing {ticker}: {e}")


def main():
    """
    The main function
    """
    logger = Logger().logger
    logger.info(f"Begin")

    try:
        run_start_time = time()

        # parser args
        args = parse_args_transform()

        # set context
        # if args.local is true
        # we'll be working with credential based AWS connection
        App.set("local", args.local)
        App.set("aws_account_id", Aws().get_account_id())  # aws dev or prod account

        # these are the lags we will apply to our TA features
        if args.lags:  # not required, default is 5
            App.set("lags", int(args.lags))

        # part 1: load data
        # reload raw data. this is the default behavior
        if args.reload:
            # crawl raw data folder to push latest updates to athena
            Glue().run_crawler(f'{App.config("aws_account_id")}-signals-crawler')

            # prepare sql script
            logger.info("Running query")
            with open("src/numerai_signals/sql/data.sql", "r") as f:
                sql_script = f.read().format(App.config("aws_account_id"))

            # run it against athena db
            (query_result, query_execution_id) = Athena().run_query(sql_script)

            # download query output if it succeded
            if query_result == "SUCCEEDED":
                S3(f"{App.config('aws_account_id')}-athena").download_file(
                    f"{query_execution_id}.csv", "data/transform/data.csv"
                )

            else:
                raise OperationalException("Reload operation failed. Exiting.")

        # part 2: transform data
        # load data into frame
        logger.info("Load data")
        df = pd.read_csv("data/transform/data.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        start_date = datetime.date.today()
        end_date = start_date - datetime.timedelta(days=540)  # 660?
        df[df["timestamp"].dt.date.between(end_date, start_date)]

        logger.info("Let's go 🔥")
        tickers = list(np.sort(df.ticker.unique()))

        # call multi thread to compute features
        mt = MultiThread()
        mt.execute(tickers, transform, {"df": df, "cmd": args.cmd})
        df_out = mt.parse_transform()

        df_out.to_csv(f"data/transform/transform.csv", index=False)

        logger.info(f"Uploading file")
        s3 = S3(f"{App.config('aws_account_id')}-signals-data")
        s3.upload_file(
            f"transform_data/updated_training.csv", f"data/transform/transform.csv"
        )

        logger.info(f"Nrows published: {len(df_out.index)}")
        _time_sec = round(time() - run_start_time, 2)
        _time_min = round(_time_sec / 60, 2)
        logger.info(f"Time taken: {_time_min} min ({_time_sec} sec)")
        logger.info("🔥")

    except Exception as e:
        logger.error(e, exc_info=True)


if __name__ == "__main__":
    main()
