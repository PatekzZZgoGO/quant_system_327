# 市场数据加载器
# data/loaders/market_loader.py
from data.ingestion.tushare_client import TushareDataFetcher
from core.common.enums import MarketDataFeed

class TushareMarketDataFeed(MarketDataFeed):
    def __init__(self):
        self.fetcher = TushareDataFetcher()

    def get_bars(self, symbol: str, start: str, end: str, frequency: str = 'daily'):
        self.fetcher.symbol = symbol
        return self.fetcher.fetch_historical_data(start, end)