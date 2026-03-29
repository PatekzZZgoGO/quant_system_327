from pathlib import Path
import pandas as pd

# loaders
from data.loaders.price_loader import PriceLoader
from data.loaders.basic_loader import BasicLoader
from data.loaders.panel_loader import PanelLoader
from data.loaders.universe_loader import UniverseLoader

# processors
from data.processors.cleaner_processor import clean_market_data

# domains
from data.domains.market_domain import Market
from data.domains.universe_domain import Universe


class DataService:
    """
    🚀 数据统一入口（工业级）

    设计原则：
    - 唯一入口
    - 返回的数据 = 已标准化
    - 上层无需再做清洗
    """

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

        self.price_loader = PriceLoader(self.data_dir)
        self.basic_loader = BasicLoader(self.data_dir)

        self.panel_loader = PanelLoader(
            self.price_loader,
            self.basic_loader
        )

        self.universe_loader = UniverseLoader(self.data_dir)

    # =========================
    # 📊 Market（核心）
    # =========================
    def get_panel(self, symbols, start, end):
        """
        返回标准化 Market Domain

        ✔ 已排序
        ✔ 已去重
        ✔ 无未来函数
        """

        panel = self.panel_loader.load_panel(symbols, start, end)

        if panel is None or panel.empty:
            return Market(panel)

        # 🚀 统一清洗（唯一入口）
        panel = clean_market_data(panel)

        return Market(panel)

    # =========================
    # 📦 Universe
    # =========================
    def get_universe(self, limit=None):
        symbols = self.universe_loader.get_universe(limit)
        return Universe(symbols)