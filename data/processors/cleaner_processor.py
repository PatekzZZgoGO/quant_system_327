def handle_missing(df, factor_cols):
    """
    全局缺失处理（可扩展）
    """

    for col in factor_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    return df