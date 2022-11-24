#region imports
from AlgorithmImports import *
#endregion
from QuantConnect.Data.UniverseSelection import *
import numpy as np

LOOKBACK_WINDOW = 252
DOLLAR_VOLUME_TOP_N = 3000
MOMENTUM_TOP_N = 100

class MomentumAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2012, 1, 1)  # Set Start Date
        self.SetEndDate(2022, 1, 1)    # Set Start Date
        self.SetCash(100000)           # Set Strategy Cash

        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction)
        self.symbolDataDict = {}
        self.AddEquity("SPY", Resolution.Daily)
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.rebalance)

    def CoarseSelectionFunction(self, coarse):
        # drop stocks which don't have fundamental data or have too low prices
        selected = [x for x in coarse if x.HasFundamentalData and (float(x.Price) > 5)]
        # rank the stocks by dollar volume
        filtered = sorted(selected, key=lambda x: x.DollarVolume, reverse=True)
        return [x.Symbol for x in filtered[:DOLLAR_VOLUME_TOP_N]]

    def rebalance(self):
        sorted_symbolData = sorted(self.symbolDataDict, key=lambda x: self.symbolDataDict[x].Momentum(), reverse=True)
        # pick stocks with the highest momentum
        long_stocks = sorted_symbolData[:MOMENTUM_TOP_N]
        stocks_invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        # liquidate stocks not in the list
        for i in stocks_invested:
            if i not in long_stocks:
                self.Liquidate(i)
        # long stocks with the highest momentum
        for i in long_stocks:
            self.SetHoldings(i, 1/MOMENTUM_TOP_N)


    def OnData(self, data):
        for symbol, symbolData in self.symbolDataDict.items():
            # update the indicator value for newly added securities
            if symbol not in self.addedSymbols:
                symbolData.Price.Add(IndicatorDataPoint(symbol, self.Time, self.Securities[symbol].Close))

        self.addedSymbols = []
        self.removedSymbols = []

    def OnSecuritiesChanged(self, changes):

        # clean up data for removed securities
        self.removedSymbols = [x.Symbol for x in changes.RemovedSecurities]
        for removed in changes.RemovedSecurities:
            symbolData = self.symbolDataDict.pop(removed.Symbol, None)

        # warm up the indicator with history price for newly added securities
        self.addedSymbols = [ x.Symbol for x in changes.AddedSecurities if x.Symbol.Value != "SPY"]
        history = self.History(self.addedSymbols, LOOKBACK_WINDOW+1, Resolution.Daily)

        for symbol in self.addedSymbols:
            if symbol not in self.symbolDataDict.keys():
                symbolData = SymbolData(symbol, LOOKBACK_WINDOW)
                self.symbolDataDict[symbol] = symbolData
                if str(symbol) in history.index:
                    symbolData.WarmUpIndicator(history.loc[str(symbol)])


class SymbolData:
    '''Contains data specific to a symbol required by this model'''

    def __init__(self, symbol, lookback):
        self.symbol = symbol
        self.Price = RollingWindow[IndicatorDataPoint](lookback)

    def WarmUpIndicator(self, history):
        # warm up the indicator with the history request
        for tuple in history.itertuples():
            item = IndicatorDataPoint(self.symbol, tuple.Index, float(tuple.close))
            self.Price.Add(item)

    def Momentum(self):
        data = [float(x.Value) for x in self.Price]
        if not data or data[-1] == 0:
            return np.nan
        return (data[0] - data[-1]) / data[-1]
