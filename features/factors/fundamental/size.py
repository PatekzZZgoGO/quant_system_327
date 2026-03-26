import numpy as np


def size(df):
    """
    👻 市值因子
    """
    return np.log(df['TotalMV'].replace(0, np.nan))
