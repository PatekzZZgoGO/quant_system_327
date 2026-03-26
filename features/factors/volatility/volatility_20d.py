def volatility_20d(df, context=None):
    """
    👻 波动率（20日）
    """
    returns = df['Close'].pct_change()
    return returns.rolling(20).std()

volatility_20d.alias = "volatility"