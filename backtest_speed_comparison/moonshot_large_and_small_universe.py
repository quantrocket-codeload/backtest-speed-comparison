
import pandas as pd
from moonshot import Moonshot
from quantrocket.master import get_securities_reindexed_like

class Momentum(Moonshot):

    CODE = None
    DB = "usstock-1d-bundle"
    DB_FIELDS = ["Close", "Volume"]
    LOOKBACK_WINDOW = 252
    DOLLAR_VOLUME_TOP_N = 3000
    MOMENTUM_TOP_N = 100
    REBALANCE_INTERVAL = None

    def prices_to_signals(self, prices):

        closes = prices.loc["Close"]

        if self.SIDS:
            in_universe = pd.DataFrame(True, index=closes.index, columns=closes.columns)
        else:
            sec_types = get_securities_reindexed_like(
                closes, fields="usstock_SecurityType2").loc["usstock_SecurityType2"]
            in_universe = sec_types == "Common Stock"

            volumes = prices.loc["Volume"]
            avg_dollar_volumes = (closes * volumes).rolling(90).mean()

            dollar_volume_ranks = avg_dollar_volumes.where(in_universe).rank(axis=1, ascending=False)
            in_universe = dollar_volume_ranks <= self.DOLLAR_VOLUME_TOP_N

        # rank by 12-month returns
        returns = (closes - closes.shift(self.LOOKBACK_WINDOW)) / closes.shift(self.LOOKBACK_WINDOW)
        # Only apply rankings to eligible stocks
        ranks =returns.where(in_universe).rank(axis=1, ascending=False)
        long_signals = ranks <= self.MOMENTUM_TOP_N

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

class MomentumLargeUniverse(Momentum):

    CODE = "moonshot-large-universe"
    REBALANCE_INTERVAL = "MS"

class MomentumSmallUniverse(Momentum):

    CODE = "moonshot-small-universe"
    SIDS = [
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
    MOMENTUM_TOP_N = 3
    REBALANCE_INTERVAL = "MS"
