import zipline.api as algo
from zipline.pipeline import Pipeline
from zipline.pipeline.data import master
from zipline.pipeline.factors import Returns, AverageDollarVolume
from zipline.finance.execution import MarketOrder

LOOKBACK_WINDOW = 252
DOLLAR_VOLUME_TOP_N = 3000
MOMENTUM_TOP_N = 100
BUNDLE = "usstock-1d-bundle"

def initialize(context):

    schedule = algo.date_rules.month_start()

    algo.schedule_function(
        rebalance,
        schedule
    )

    # Create a pipeline to select stocks each day.
    algo.attach_pipeline(make_pipeline(), 'pipeline')

def make_pipeline():
    """
    Create a pipeline to select stocks each day.
    """

    sec_type = master.SecuritiesMaster.usstock_SecurityType2.latest
    in_universe = sec_type.eq("Common Stock")

    avg_dollar_volume = AverageDollarVolume(
        window_length=90,
        mask=in_universe)
    in_universe = avg_dollar_volume.top(DOLLAR_VOLUME_TOP_N)


    returns = Returns(window_length=LOOKBACK_WINDOW, mask=in_universe)

    pipe = Pipeline(
        screen=returns.top(MOMENTUM_TOP_N)
    )
    return pipe

def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = algo.pipeline_output('pipeline')
    context.desired_portfolio = context.output.index

def rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing.
    """
    positions = context.portfolio.positions

    target_pct = 1 / MOMENTUM_TOP_N

    # open new positions
    for asset in context.desired_portfolio:
        if asset in positions:
            continue
        algo.order_target_percent(
            asset, target_pct, style=MarketOrder())

    for asset in positions:

        # close positions we no longer want
        if asset not in context.desired_portfolio:
            algo.order_target_percent(asset, 0, style=MarketOrder())
