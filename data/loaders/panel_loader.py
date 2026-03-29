import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from data.processors.aligner_processor import align_price_basic

class PanelLoader:

    def __init__(self, price_loader, basic_loader):
        self.price_loader = price_loader
        self.basic_loader = basic_loader

    def _load_one(self, symbol, start, end):

        price = self.price_loader.load(symbol, start, end)

        if price.empty:
            return None

        basic = self.basic_loader.load(symbol)

        if not basic.empty:
            df = align_price_basic(price, basic)
        else:
            df = price

        df["Symbol"] = symbol

        return df

    def load_panel(self, symbols, start, end, max_workers=8):

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self._load_one, s, start, end)
                for s in symbols
            ]

            for f in futures:
                df = f.result()
                if df is not None and not df.empty:
                    results.append(df)

        if not results:
            return pd.DataFrame()

        panel = pd.concat(results, ignore_index=True)

        panel = panel.sort_values(["Symbol", "Date"])
        panel = panel.drop_duplicates(["Date", "Symbol"])

        return panel