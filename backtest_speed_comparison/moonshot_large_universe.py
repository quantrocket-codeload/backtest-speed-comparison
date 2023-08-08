from moonshot import Moonshot
from quantrocket.fundamental import get_sharadar_fundamentals_reindexed_like

class PiotroskiFScore(Moonshot):

    CODE = "moonshot-large-universe"
    DB = "sharadar-1d"
    DB_FIELDS = ["Close"]
    MIN_F_SCORE = 7
    MARKETCAP_TOP_N = 1000
    REBALANCE_INTERVAL = "M"

    def prices_to_signals(self, prices):

        closes = prices.loc["Close"]
        marketcaps = get_sharadar_fundamentals_reindexed_like(
            closes, fields="MARKETCAP", dimension="ART").loc["MARKETCAP"]
        marketcap_ranks = marketcaps.rank(axis=1, ascending=False)
        in_universe = marketcap_ranks <= self.MARKETCAP_TOP_N

        f_scores = get_f_scores(closes)
        long_signals = in_universe & (f_scores >= self.MIN_F_SCORE)

        return long_signals.astype(int)

    def signals_to_target_weights(self, signals, prices):
        # Step 4: equal weights
        daily_signal_counts = signals.abs().sum(axis=1)
        weights = signals.div(daily_signal_counts, axis=0).fillna(0)

        if self.REBALANCE_INTERVAL:
            # Step 5: Rebalance monthly
            # Resample daily to monthly, taking the last day's signal
            # For pandas offset aliases, see https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
            weights = weights.resample(self.REBALANCE_INTERVAL).last()
            # Reindex back to daily and fill forward
            weights = weights.reindex(prices.loc["Close"].index, method="ffill")

        return weights

    def target_weights_to_positions(self, weights, prices):
        # Enter the position the day after the signal
        return weights.shift()

    def positions_to_gross_returns(self, positions, prices):

        closes = prices.loc["Close"]
        position_ends = positions.shift()

        # The return is the security's percent change over the period,
        # multiplied by the position.
        gross_returns = closes.pct_change() * position_ends

        return gross_returns

def get_f_scores(closes):

    # Step 1: query relevant indicators
    fundamentals = get_sharadar_fundamentals_reindexed_like(
       closes,
       dimension="ART", # As-reported trailing twelve month reports
       fields=[
           "ROA", # Return on assets
           "ASSETS", # Total Assets
           "NCFO", # Net Cash Flow from Operations
           "DE", # Debt to Equity Ratio
           "CURRENTRATIO", # Current ratio
           "SHARESWA", # Outstanding shares
           "GROSSMARGIN", # Gross margin
           "ASSETTURNOVER", # Asset turnover
       ])
    return_on_assets = fundamentals.loc["ROA"]
    total_assets = fundamentals.loc["ASSETS"]
    operating_cash_flows = fundamentals.loc["NCFO"]
    leverages = fundamentals.loc["DE"]
    current_ratios = fundamentals.loc["CURRENTRATIO"]
    shares_out = fundamentals.loc["SHARESWA"]
    gross_margins = fundamentals.loc["GROSSMARGIN"]
    asset_turnovers = fundamentals.loc["ASSETTURNOVER"]

    # Step 2: many Piotroski F-score components compare current to previous
    # values, so get DataFrames of previous values

    # Step 2.a: get a boolean mask of the first day of each newly reported fiscal
    # period
    fundamentals = get_sharadar_fundamentals_reindexed_like(
        closes,
        dimension="ART", # As-reported trailing twelve month reports
        fields=["REPORTPERIOD"])
    fiscal_periods = fundamentals.loc["REPORTPERIOD"]
    are_new_fiscal_periods = fiscal_periods != fiscal_periods.shift()

    # Step 2.b: shift the ROAs forward one fiscal period by (1) shifting the ratios one day,
    # (2) keeping only the ones that fall on the first day of the newly reported
    # fiscal period, and (3) forward-filling
    previous_return_on_assets = return_on_assets.shift().where(are_new_fiscal_periods).fillna(method="ffill")

    # Step 2.c: Repeat for other indicators
    previous_leverages = leverages.shift().where(are_new_fiscal_periods).fillna(method="ffill")
    previous_current_ratios = current_ratios.shift().where(are_new_fiscal_periods).fillna(method="ffill")
    previous_shares_out = shares_out.shift().where(are_new_fiscal_periods).fillna(method="ffill")
    previous_gross_margins = gross_margins.shift().where(are_new_fiscal_periods).fillna(method="ffill")
    previous_asset_turnovers = asset_turnovers.shift().where(are_new_fiscal_periods).fillna(method="ffill")

    # Step 3: calculate F-Score components; each resulting component is a DataFrame
    # of booleans
    have_positive_return_on_assets = return_on_assets > 0
    have_positive_operating_cash_flows = operating_cash_flows > 0
    have_increasing_return_on_assets = return_on_assets > previous_return_on_assets
    have_more_cash_flow_than_incomes = operating_cash_flows / total_assets > return_on_assets
    have_decreasing_leverages = leverages < previous_leverages
    have_increasing_current_ratios = current_ratios > previous_current_ratios
    have_no_new_shares = shares_out <= previous_shares_out
    have_increasing_gross_margins = gross_margins > previous_gross_margins
    have_increasing_asset_turnovers = asset_turnovers > previous_asset_turnovers

    # Step 4: convert the booleans to integers and sum to get F-Score (0-9)
    f_scores = (
        have_positive_return_on_assets.astype(int)
        + have_positive_operating_cash_flows.astype(int)
        + have_increasing_return_on_assets.astype(int)
        + have_more_cash_flow_than_incomes.astype(int)
        + have_decreasing_leverages.astype(int)
        + have_increasing_current_ratios.astype(int)
        + have_no_new_shares.astype(int)
        + have_increasing_gross_margins.astype(int)
        + have_increasing_asset_turnovers.astype(int)
    )
    return f_scores

class PiotroskiFScoreSmallUniverse(PiotroskiFScore):

    CODE = "moonshot-small-universe"
    SIDS = [
        "FIBBG000B9XRY4", # AAPL
        "FIBBG000BVPV84", # AMZN
        "FIBBG000BMHYD1", # JNJ
        "FIBBG000BKZB36", # HD
        "FIBBG000GZQ728", # XOM
        "FIBBG000BPH459", # MSFT
        "FIBBG000BNSZP1", # MCD
        "FIBBG000L9CV04", # UPS
        "FIBBG000CH5208", # UNH
        "FIBBG000HS77T5", # VZ
    ]
