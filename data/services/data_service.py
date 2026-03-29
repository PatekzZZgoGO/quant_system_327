from pathlib import Path

# loaders
from data.loaders.price_loader import PriceLoader
from data.loaders.basic_loader import BasicLoader
from data.loaders.panel_loader import PanelLoader
from data.loaders.universe_loader import UniverseLoader

# domains
from data.domains.market_domain import Market
from data.domains.universe_domain import Universe


class DataService:
    """
    数据统一入口（唯一对外接口）

    设计原则：
    - 上层（IC / Factor / Backtest）只依赖 DataService
    - 不允许直接调用 loader
    """

    def __init__(self, data_dir: str):

        self.data_dir = Path(data_dir)

        # loaders（IO）
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
        返回 Market Domain
        """

        panel = self.panel_loader.load_panel(symbols, start, end)

        return Market(panel)

    # =========================
    # 📦 Universe（股票池）
    # =========================
    def get_universe(self, limit=None):
        """
        返回 Universe Domain
        """

        symbols = self.universe_loader.get_universe(limit)

        return Universe(symbols)