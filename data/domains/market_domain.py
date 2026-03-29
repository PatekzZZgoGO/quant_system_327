class Market:
    """
    市场数据语义封装（不是 IO）
    """

    def __init__(self, panel):
        self.panel = panel

    def get_snapshot(self, date):
        return self.panel[self.panel["Date"] == date]

    def symbols(self):
        return self.panel["Symbol"].unique()

    def dates(self):
        return sorted(self.panel["Date"].unique())