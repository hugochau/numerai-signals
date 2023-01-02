"""
transform.py

Main script for transforming raw data
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

from time import time
import datetime

import pandas as pd

from module.logger.logger import Logger
from module.exception import OperationalException
from module.s3 import S3
from module.athena import Athena
from module.multi_thread import MultiThread
from module.aws import Aws
from module.app import App
from module.transformer import Transformer
from util.parse_args import parse_args_transform
from util.optimise_frame import optimise_frame


def transform(params):
    logger = Logger().logger
    df = params["params"]["df"]
    ticker = params["task"]

    try:
        trans = Transformer()

        # Create a final frame with the transformed tickers
        df_ticker = df[df["ticker"] == ticker]
        # derniere date=aujourd'hui=derniere ligne
        df_ticker.sort_values(by=["timestamp"], inplace=True)

        # This is where the magic happens
        df_ticker = getattr(trans, f"{args.cmd}_indicators")(df_ticker)
        for i in df_ticker.columns[3:]:
            df_ticker = trans.shifter(df_ticker, i)

        df_ticker = optimise_frame(df_ticker)
        df_ticker = df_ticker[df_ticker["timestamp"].dt.weekday == 4]

        return df_ticker

    except BaseException as e:
        logger.error(f"Error while processing {ticker}: {e}")


if __name__ == "__main__":
    logger = Logger().logger
    run_start_time = time()
    logger.info(f"Begin")

    # parser args
    args = parse_args_transform()

    # set context
    App.set("local", args.local)
    App.set("aws_account_id", Aws().get_account_id())

    if args.reload:
        logger.info("Running query")
        with open("src/numerai_signals/sql/data.sql", "r") as f:
            sql_script = f.read().format(App.config("aws_account_id"))

        # sql_blocks = sql_script.split(';')
        (query_result, query_execution_id) = Athena().run_query(sql_script)

        if query_result == "SUCCEEDED":
            S3(f"{App.config('aws_account_id')}-athena").download_file(
                f"{query_execution_id}.csv", "data/transform/data.csv"
            )

        else:
            raise OperationalException("Reload operation failed. Exiting.")

    logger.info("Load data")
    df = pd.read_csv("data/transform/data.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    start_date = datetime.date.today()
    end_date = start_date - datetime.timedelta(days=540)  # 660?
    df[df["timestamp"].dt.date.between(end_date, start_date)]

    # Declare the variables that will be required later
    if args.lags:
        App.set("lags", int(args.lags))

    logger.info("Let's go 🔥")
    tickers = list(df.ticker.unique())

    # call multi thread to compute features
    mt = MultiThread()
    mt.execute(tickers, transform, {"df": df})
    df_out = mt.parse_transform()

    # df_out.to_parquet(f"data/transform/transform.parquet", index=False)
    df_out.to_csv(f"data/transform/transform.csv", index=False)

    logger.info(f"Uploading file")
    s3 = S3(f"{App.config('aws_account_id')}-signals-data")
    s3.upload_file(
        f"transform_data/updated_training.csv", f"data/transform/transform.csv"
    )

    logger.info(f"Nrows published: {len(df_out.index)}")

    _time = round(time() - run_start_time, 2)
    logger.info(f"Time taken: {_time/60}min ({_time}sec)")
    logger.info("🔥")
