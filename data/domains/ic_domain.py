import pandas as pd
import logging

logger = logging.getLogger(__name__)


class IC:
    """
    📊 IC Domain（信息系数计算）

    职责：
    - 统一处理 zscore（横截面）
    - 计算 IC（Spearman）
    - 输出标准 IC DataFrame

    输入：
        panel（必须包含）
        Date | Symbol | factors | ret_xx

    输出：
        Date | factor | ic
    """

    def __init__(self, panel: pd.DataFrame):
        self.panel = panel.copy()

    # =========================
    # 🧠 横截面标准化（核心）
    # =========================
    def _zscore(self, df: pd.DataFrame, factors):
        """
        Cross-sectional zscore（按 Date）
        """

        for f in factors:
            if f not in df.columns:
                continue

            z_col = f"{f}_z"

            df[z_col] = (
                df.groupby("Date")[f]
                .transform(lambda x: (x - x.mean()) / (x.std() + 1e-8))
            )

        return df

    # =========================
    # 📈 IC 计算（核心）
    # =========================
    def compute(
        self,
        factors,
        ret_col,
        method="spearman"
    ):
        """
        计算 IC（向量化 groupby）

        返回：
            DataFrame:
            Date | factor | ic
        """

        df = self.panel.copy()

        # =========================
        # 1️⃣ 检查列
        # =========================
        missing = [f for f in factors if f not in df.columns]

        if missing:
            logger.warning(f"[IC] Missing raw factors: {missing}")
            factors = [f for f in factors if f in df.columns]

        if not factors:
            logger.error("[IC] No valid factors")
            return pd.DataFrame()

        if ret_col not in df.columns:
            logger.error(f"[IC] Missing return column: {ret_col}")
            return pd.DataFrame()

        # =========================
        # 2️⃣ 标准化（关键）
        # =========================
        df = self._zscore(df, factors)

        factor_cols = [f"{f}_z" for f in factors]

        # =========================
        # 3️⃣ dropna
        # =========================
        use_cols = ["Date", ret_col] + factor_cols

        df = df[use_cols].dropna()

        if df.empty:
            logger.error("[IC] Empty after dropna")
            return pd.DataFrame()

        logger.info(f"[IC] IC input shape: {df.shape}")

        # =========================
        # 4️⃣ groupby IC
        # =========================
        def compute_ic_block(x):

            if len(x) < 5:
                return pd.Series(
                    [None] * len(factor_cols),
                    index=factor_cols
                )

            return x[factor_cols].corrwith(
                x[ret_col],
                method=method
            )

        ic_matrix = df.groupby("Date").apply(compute_ic_block)

        # =========================
        # 5️⃣ 转长表
        # =========================
        ic_df = (
            ic_matrix
            .stack()
            .reset_index()
            .rename(columns={
                "level_1": "factor",
                0: "ic"
            })
        )

        # 去掉 _z
        ic_df["factor"] = ic_df["factor"].str.replace("_z", "")

        return ic_df