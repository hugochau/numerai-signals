"""
parse_args.py

Define parse_args functions
"""

import argparse
from datetime import datetime


def validate_load_args(**kwargs):
    """
    Validate kwargs args format
    """
    # validate date range is in ascending order
    if "start" in kwargs and "end" in kwargs:
        try:
            assert int(kwargs["start"]) < int(kwargs["end"])

        except AssertionError as e:
            raise e

        # validate date format
        # raise ValueError
        try:
            datetime.strptime(kwargs["start"], "%y%m%d")
            datetime.strptime(kwargs["end"], "%y%m%d")

        except ValueError as e:
            raise e

    if "ntickers" in kwargs and kwargs["ntickers"] is not None:
        # validate ntickers > 0
        try:
            assert int(kwargs["ntickers"]) > 0

        except AssertionError as e:
            raise e


def parse_args_load():
    """
    Parse CLI arguments for load entry point
    Validate format

    ::return parsed and validated CLI arguments
    """
    parser = argparse.ArgumentParser()

    # crawler start date
    parser.add_argument(
        "--start", required=True, type=str, help="start date format YYMMDD"
    )

    # crawler end date
    # must be greater than args.start
    parser.add_argument(
        "--end", required=True, type=str, help="start date format YYMMDD"
    )

    # test on a subset of numerai tickers
    parser.add_argument(
        "--ntickers",
        required=False,
        default=None,
        type=int,
        help="Limit to the first n tickers",
    )

    # load given ticker
    parser.add_argument(
        "--ticker",
        required=False,
        default=None,
        type=str,
        help="Load a given ticker",
    )

    parser = parse_args_all(parser)

    # parse and validate args
    args = parser.parse_args()
    validate_load_args(start=args.start, end=args.end, ntickers=args.ntickers)

    return args


def parse_args_transform():
    """
    Parse CLI arguments for transform entry point

    ::return parsed CLI
    """
    parser = argparse.ArgumentParser()

    # TA command
    parser.add_argument(
        "--cmd",
        choices=["all", "momentum", "other", "trend", "volatility", "volume"],
        required=True,
        type=str,
        help=" please choose from: all, momentum, other, trend,volatility, volume",
    )

    # reload raw data
    parser.add_argument(
        "--reload",
        required=False,
        action="store_const",
        const="_test",
        default="",
        help=" whether to reload data or not",
    )

    # define metric lags
    parser.add_argument(
        "--lags", required=False, type=str, help="How many lags you want to apply"
    )

    parser = parse_args_all(parser)

    return parser.parse_args()


def parse_args_all(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add common arguments

    ::param parser
    :: return parser, incl. common args
    """
    # will tell AWS to load credential from file
    parser.add_argument(
        "--local", required=False, action="store_const", const=True, default=False
    )

    return parser
