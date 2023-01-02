"""
optimise_frame.py

Implements optimise_frame
"""

__author__ = "Julien Lefebvre, Hugo Chauvary"
__email__ = "numerai_2021@protonmail.com"

import pandas as pd
import numpy as np


def optimise_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function optimises the total memory used in pandas

    ::param df: non optimized dataframe

    ::return df: optmized dataframe
    """
    # round to 4 decimals
    fcols = df.select_dtypes(include=[np.float, np.int]).columns
    df[fcols] = df[fcols].round(4)
    df[fcols] = df[fcols].astype("float32")

    # fcols = df.select_dtypes(include=[np.int]).columns
    # df[fcols] = df[fcols].round(4)
    # df[fcols] = df[fcols].astype("float32")

    return df
