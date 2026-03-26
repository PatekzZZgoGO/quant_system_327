def liquidity(df, context=None):
    """
    👻 流动性（换手率）
    """
    return df['TurnoverRate']