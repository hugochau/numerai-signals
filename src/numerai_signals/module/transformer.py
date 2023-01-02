"""
s3.py

Implements Transform
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

import ta
import pandas as pd

from module.app import App


class Transformer:
    """
    Main class for implementing transform operations
    resulting in technical analysis common metrics
    """

    # @staticmethod
    # def optimise_frame(df: pd.DataFrame) -> pd.DataFrame:
    #     """
    #     This function optimises the total memory used in pandas

    #     ::param df: non optimized dataframe

    #     ::return df: optmized dataframe
    #     """
    #     # df.drop(
    #     #     columns=["open", "close", "high", "low", "provider", "volume"],
    #     #     inplace=True,
    #     #     errors="ignore",
    #     # )

    #     # convert float32 to float16
    #     fcols = df.select_dtypes("float32").columns
    #     df[fcols] = df[fcols].astype("float16")

    #     # round to 4 decimals
    #     fcols = df.select_dtypes("float").columns
    #     df[fcols] = df[fcols].round(4)

    #     return df

    # @staticmethod
    # def grouper(df, ticker_col, ticker_name):
    #     """Segregate dataframes into ticker based chunks"""
    #     grouped = df.groupby([str(ticker_col)])
    #     one_frame = grouped.get_group(str(ticker_name))
    #     return one_frame

    @staticmethod
    def shifter(df: pd.DataFrame, column: str):
        """
        The shifter shifts a specific column
        and adds it to the dataframe with the prefix 'FEATURE'

        ::param df: input ddataframe
        ::param column: column to be shifted
        """
        df.rename(columns={column: f"FEATURE_{column}_shift0"}, inplace=True)

        for x in range(1, App.config("lags")):
            df[f"FEATURE_{column}_shift" + str(x)] = df[
                f"FEATURE_{column}_shift0"
            ].shift(x)

        # df.dropna(inplace=True)

        return df

    @staticmethod
    def volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Function to add volatility technical indicators
        without actually passing the columns
        """
        df = ta.add_volatility_ta(
            df, high="high", low="low", close="close", fillna=True
        )
        return df

    @staticmethod
    def momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Function to add all momentum indicators
        without actually passing the columns

        ::param
        ::return
        """
        df = ta.add_momentum_ta(
            df, high="high", low="low", close="close", volume="volume", fillna=True
        )
        return df

    @staticmethod
    def trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Function to add trend indicators
        without actually passing the columns

        ::param
        ::return
        """
        df = ta.add_trend_ta(df, high="high", low="low", close="close", fillna=True)
        return df

    @staticmethod
    def other_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Function to add other technical indicators
        without actually passing the columns

        ::param
        ::return
        """
        df = ta.add_others_ta(df, close="adj_close", fillna=True)
        return df

    @staticmethod
    def volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Function to add volume indicators
        without actually passing the columns

        ::param
        ::return
        """
        df = ta.add_volume_ta(
            df, high="high", low="low", close="close", volume="volume", fillna=True
        )
        return df

    @staticmethod
    def all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Function to add all technical indicators
        without actually passing the columns

        ::param
        ::return
        """
        df = ta.add_all_ta_features(
            df,
            open="open",
            high="high",
            low="low",
            close="close",
            volume="volume",
            fillna=True,
        )
        return df
