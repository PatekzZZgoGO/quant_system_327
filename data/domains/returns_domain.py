from data.processors.returns_processor import compute_future_returns

class Returns:
    """
    收益语义封装
    """

    def __init__(self, panel):
        self.panel = panel

    def forward(self, horizon=5):
        return compute_future_returns(self.panel, horizon)