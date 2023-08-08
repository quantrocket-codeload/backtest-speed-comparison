import zipline.api as algo
from zipline.pipeline import Pipeline, sharadar
from zipline.finance.execution import MarketOrder

MARKETCAP_TOP_N = 1000
BUNDLE = "sharadar-1d"

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

    in_universe = sharadar.Fundamentals.slice("ART").MARKETCAP.latest.top(MARKETCAP_TOP_N)
    f_score = sharadar.PiotroskiFScore(mask=in_universe)

    pipe = Pipeline(
        screen=f_score >= 7
    )
    return pipe

def rebalance(context, data):
    """
    Execute orders according to our schedule_function() timing.
    """
    context.output = algo.pipeline_output('pipeline')
    context.desired_portfolio = context.output.index

    positions = context.portfolio.positions

    target_pct = 1 / len(context.desired_portfolio)

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
