import pandas as pd
import logging

from exceptions.data import SchemaValidationError

logger = logging.getLogger(__name__)


def compute_future_returns(
    panel: pd.DataFrame,
    horizon: int = 5
) -> pd.DataFrame:
    """
    🚀 向量化 future return（无副作用 + 不丢列）

    设计原则：
    - ✔ 保留所有原始列（包括因子）
    - ✔ 只新增 ret_xd
    - ✔ 不做列裁剪（避免破坏上层）

    输入：
        panel:
        Date | Symbol | Close | factors...

    输出：
        panel + ret_xd
    """

    if panel is None or panel.empty:
        logger.warning("[Returns] Input panel is empty")
        return pd.DataFrame()

    required_cols = {"Date", "Symbol", "Close"}
    if not required_cols.issubset(panel.columns):
        raise SchemaValidationError(
            f"[Returns] Missing required columns: {required_cols - set(panel.columns)}"
        )

    df = panel.copy()

    # =========================
    # 1️⃣ 排序（极其关键）
    # =========================
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Symbol", "Date"])

    # =========================
    # 2️⃣ future close
    # =========================
    df["future_close"] = (
        df.groupby("Symbol")["Close"]
        .shift(-horizon)
    )

    # =========================
    # 3️⃣ return
    # =========================
    ret_col = f"ret_{horizon}d"

    df[ret_col] = df["future_close"] / df["Close"] - 1

    # =========================
    # 4️⃣ 清理（只 drop ret）
    # =========================
    df = df.dropna(subset=[ret_col])

    # ⚠️ 不删除 future_close（方便 debug）
    # 如果你想干净一点可以最后 drop

    logger.info(f"[Returns] Future return computed | shape={df.shape}")

    return df
