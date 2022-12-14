#region imports
from AlgorithmImports import *
#endregion

import pandas as pd
from datetime import datetime

class SelectedStocksMomentumAlgorithm(QCAlgorithm):

    def Initialize(self):

        self.SetStartDate(2012, 1, 1)
        self.SetEndDate(2022, 1, 1)
        self.SetCash(100000)
        # create a dictionary to store momentum indicators for all symbols
        self.data = {}
        period = 12*21
        self.symbols = ["SPY", "EFA", "BND", "VNQ", "GSG", "TLT", "QQQ", "IWM", "GLD", "DIA"]
        # warm up the MOM indicator
        self.SetWarmUp(period)
        for symbol in self.symbols:
            self.AddEquity(symbol, Resolution.Daily)
            self.data[symbol] = self.MOM(symbol, period, Resolution.Daily)
        # shcedule the function to fire at the month start
        self.Schedule.On(self.DateRules.MonthStart("SPY"), self.TimeRules.AfterMarketOpen("SPY"), self.Rebalance)

    def OnData(self, data):
        pass

    def Rebalance(self):
        if self.IsWarmingUp: return
        top3 = pd.Series(self.data).sort_values(ascending = False)[:3]
        for kvp in self.Portfolio:
            security_hold = kvp.Value
            # liquidate the security which is no longer in the top3 momentum list
            if security_hold.Invested and (security_hold.Symbol.Value not in top3.index):
                self.Liquidate(security_hold.Symbol)

        added_symbols = []
        for symbol in top3.index:
            if not self.Portfolio[symbol].Invested:
                added_symbols.append(symbol)
        for added in added_symbols:
            self.SetHoldings(added, 1/len(added_symbols))
