class Universe:
    """
    股票池语义层（Domain）
    """

    def __init__(self, symbols):
        self.symbols = symbols

    def limit(self, n: int):
        return Universe(self.symbols[:n])

    def size(self):
        return len(self.symbols)

    def head(self, n=5):
        return self.symbols[:n]

    def __repr__(self):
        return f"<Universe size={len(self.symbols)}>"