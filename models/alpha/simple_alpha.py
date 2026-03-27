# models/alpha/simple_alpha.py

def get_weights(date=None):
    return {
        "momentum_20d": 1.0,
        "volatility_20d": -1.0,
        "liquidity": 0.5,
    }


TOP_N = 50