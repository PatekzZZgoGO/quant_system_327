def momentum_20d(df, context=None):
    return df['Close'].pct_change(20)

# 👇 注册别名
momentum_20d.alias = "momentum"