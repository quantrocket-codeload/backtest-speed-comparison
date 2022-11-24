import zipline.api as algo
from zipline.finance.execution import MarketOrder

LOOKBACK_WINDOW = 252
BUNDLE = "usstock-1d-bundle"

def initialize(context):

    schedule = algo.date_rules.month_start()

    algo.schedule_function(
        rebalance,
        schedule
    )

    context.sids = [
        "FIBBG000BDTBL9", # SPY
        "FIBBG000BJKYW3", # TLT
        "FIBBG000BSWKH7", # QQQ
        "FIBBG000BTDS98", # DIA
        "FIBBG000BZZS63", # BND
        "FIBBG000CGC9C4", # IWM
        "FIBBG000CRF6Q8", # GLD
        "FIBBG000D2KQ55", # EFA
        "FIBBG000PVYFK0", # GSG
        "FIBBG000Q89NG6", # VNQ
    ]

def rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing.
    """
    assets = [algo.sid(sid) for sid in context.sids]

    closes = data.history(assets, "close", LOOKBACK_WINDOW, "1d")
    returns = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]

    assets_to_buy = returns.sort_values(ascending=False).index[:3]

    positions = context.portfolio.positions

    for asset in positions:
        if asset not in assets_to_buy:
            algo.order_target_percent(asset, 0, style=MarketOrder())

    for asset in assets_to_buy:
        if asset not in positions:
            algo.order_target_percent(asset, 1/3, style=MarketOrder())
