# Adapted from Piotroski-F-Score-Investing strategy in QuantConnect Research Library:
# https://www.quantconnect.com/explore/15314047/Piotroski-F-Score-Investing

# region imports
from AlgorithmImports import *
# endregion

def GetROAScore(fine):
    '''Get the Profitability - Return of Asset sub-score of Piotroski F-Score
    Arg:
        fine: Fine fundamental object of a stock
    Return:
        Profitability - Return of Asset sub-score'''
    # Nearest ROA as current year data
    roa = fine.OperationRatios.ROA.ThreeMonths
    # 1 score if ROA datum exists and positive, else 0
    score = 1 if roa and roa > 0 else 0
    return score

def GetOperatingCashFlowScore(fine):
    '''Get the Profitability - Operating Cash Flow sub-score of Piotroski F-Score
    Arg:
        fine: Fine fundamental object of a stock
    Return:
        Profitability - Operating Cash Flow sub-score'''
    # Nearest Operating Cash Flow as current year data
    operating_cashflow = fine.FinancialStatements.CashFlowStatement.CashFlowFromContinuingOperatingActivities.ThreeMonths
    # 1 score if operating cash flow datum exists and positive, else 0
    score = 1 if operating_cashflow and operating_cashflow > 0 else 0
    return score

def GetROAChangeScore(fine):
    '''Get the Profitability - Change in Return of Assets sub-score of Piotroski F-Score
    Arg:
        fine: Fine fundamental object of a stock
    Return:
        Profitability - Change in Return of Assets sub-score'''
    # if current or previous year's ROA data does not exist, return 0 score
    roa = fine.OperationRatios.ROA
    if not roa.ThreeMonths or not roa.OneYear:
        return 0

    # 1 score if change in ROA positive, else 0 score
    score = 1 if roa.ThreeMonths > roa.OneYear else 0
    return score

def GetAccrualsScore(fine):
    '''Get the Profitability - Accruals sub-score of Piotroski F-Score
    Arg:
        fine: Fine fundamental object of a stock
    Return:
        Profitability - Accruals sub-score'''
    # Nearest Operating Cash Flow, Total Assets, ROA as current year data
    operating_cashflow = fine.FinancialStatements.CashFlowStatement.CashFlowFromContinuingOperatingActivities.ThreeMonths
    total_assets = fine.FinancialStatements.BalanceSheet.TotalAssets.ThreeMonths
    roa = fine.OperationRatios.ROA.ThreeMonths
    # 1 score if operating cash flow, total assets and ROA exists, and operating cash flow / total assets > ROA, else 0
    score = 1 if operating_cashflow and total_assets and roa and operating_cashflow / total_assets > roa else 0
    return score

def GetLeverageScore(fine):
    '''Get the Leverage, Liquidity and Source of Funds - Change in Leverage sub-score of Piotroski F-Score
    Arg:
        fine: Fine fundamental object of a stock
    Return:
        Leverage, Liquidity and Source of Funds - Change in Leverage sub-score'''
    # if current or previous year's long term debt to equity ratio data does not exist, return 0 score
    long_term_debt_ratio = fine.OperationRatios.LongTermDebtEquityRatio
    if not long_term_debt_ratio.ThreeMonths or not long_term_debt_ratio.OneYear:
        return 0

    # 1 score if long term debt ratio is lower in the current year, else 0 score
    score = 1 if long_term_debt_ratio.ThreeMonths < long_term_debt_ratio.OneYear else 0
    return score

def GetLiquidityScore(fine):
    '''Get the Leverage, Liquidity and Source of Funds - Change in Liquidity sub-score of Piotroski F-Score
    Arg:
        fine: Fine fundamental object of a stock
    Return:
        Leverage, Liquidity and Source of Funds - Change in Liquidity sub-score'''
    # if current or previous year's current ratio data does not exist, return 0 score
    current_ratio = fine.OperationRatios.CurrentRatio
    if not current_ratio.ThreeMonths or not current_ratio.OneYear:
        return 0

    # 1 score if current ratio is higher in the current year, else 0 score
    score = 1 if current_ratio.ThreeMonths > current_ratio.OneYear else 0
    return score

def GetShareIssuedScore(fine):
    '''Get the Leverage, Liquidity and Source of Funds - Change in Number of Shares sub-score of Piotroski F-Score
    Arg:
        fine: Fine fundamental object of a stock
    Return:
        Leverage, Liquidity and Source of Funds - Change in Number of Shares sub-score'''
    # if current or previous year's issued shares data does not exist, return 0 score
    shares_issued = fine.FinancialStatements.BalanceSheet.ShareIssued
    if not shares_issued.ThreeMonths or not shares_issued.TwelveMonths:
        return 0

    # 1 score if shares issued did not increase in the current year, else 0 score
    score = 1 if shares_issued.ThreeMonths <= shares_issued.TwelveMonths else 0
    return score

def GetGrossMarginScore(fine):
    '''Get the Leverage, Liquidity and Source of Funds - Change in Gross Margin sub-score of Piotroski F-Score
    Arg:
        fine: Fine fundamental object of a stock
    Return:
        Leverage, Liquidity and Source of Funds - Change in Gross Margin sub-score'''
    # if current or previous year's gross margin data does not exist, return 0 score
    gross_margin = fine.OperationRatios.GrossMargin
    if not gross_margin.ThreeMonths or not gross_margin.OneYear:
        return 0

    # 1 score if gross margin is higher in the current year, else 0 score
    score = 1 if gross_margin.ThreeMonths > gross_margin.OneYear else 0
    return score

def GetAssetTurnoverScore(fine):
    '''Get the Leverage, Liquidity and Source of Funds - Change in Asset Turnover Ratio sub-score of Piotroski F-Score
    Arg:
        fine: Fine fundamental object of a stock
    Return:
        Leverage, Liquidity and Source of Funds - Change in Asset Turnover Ratio sub-score'''
    # if current or previous year's asset turnover data does not exist, return 0 score
    asset_turnover = fine.OperationRatios.AssetsTurnover
    if not asset_turnover.ThreeMonths or not asset_turnover.OneYear:
        return 0

    # 1 score if asset turnover is higher in the current year, else 0 score
    score = 1 if asset_turnover.ThreeMonths > asset_turnover.OneYear else 0
    return score

MARKETCAP_TOP_N = 1000

class FScoreUniverseSelectionModel(FineFundamentalUniverseSelectionModel):

    def __init__(self, algorithm, fscore_threshold):
        super().__init__(self.SelectCoarse, self.SelectFine)
        self.algorithm = algorithm
        self.fscore_threshold = fscore_threshold

    def SelectCoarse(self, coarse):
        '''Defines the coarse fundamental selection function.
        Args:
            algorithm: The algorithm instance
            coarse: The coarse fundamental data used to perform filtering
        Returns:
            An enumerable of symbols passing the filter'''
        filtered = [x.Symbol for x in coarse if x.HasFundamentalData]

        return filtered

    def SelectFine(self, fine):
        '''Defines the fine fundamental selection function.
        Args:
            algorithm: The algorithm instance
            fine: The fine fundamental data used to perform filtering
        Returns:
            An enumerable of symbols passing the filter'''
        # We use a dictionary to hold the F-Score of each stock
        f_scores = {}

        fine = sorted(fine, key=lambda x: x.MarketCap, reverse=True)[:MARKETCAP_TOP_N]

        for f in fine:
            # Calculate the Piotroski F-Score of the given stock
            f_scores[f.Symbol] = self.GetPiotroskiFScore(f)

        # Select the stocks with F-Score higher than the threshold
        selected = [symbol for symbol, fscore in f_scores.items() if fscore >= self.fscore_threshold]

        return selected

    def GetPiotroskiFScore(self, fine):
        '''A helper function to calculate the Piotroski F-Score of a stock
        Arg:
            fine: MorningStar fine fundamental data of the stock
        return:
            the Piotroski F-Score of the stock
        '''
        # initial F-Score as 0
        fscore = 0
        # Add up the sub-scores in different aspects
        fscore += GetROAScore(fine)
        fscore += GetOperatingCashFlowScore(fine)
        fscore += GetROAChangeScore(fine)
        fscore += GetAccrualsScore(fine)
        fscore += GetLeverageScore(fine)
        fscore += GetLiquidityScore(fine)
        fscore += GetShareIssuedScore(fine)
        fscore += GetGrossMarginScore(fine)
        fscore += GetAssetTurnoverScore(fine)
        return fscore

# wrap ConstantAlphaModel to only rebalance monthly; see
# https://www.quantconnect.com/forum/discussion/7977/modifying-insight-duration-within-bootcamp-algorithm-framework/p1/comment-22242
class AlphaModel(ConstantAlphaModel):

    def __init__(self, *args, **kwargs):
        self.month = -1
        super().__init__(*args, **kwargs)

    def Update(self, algorithm, data):
        if self.month == algorithm.Time.month:
            return []
        self.month = algorithm.Time.month
        return super().Update(algorithm, data)

class PiotroskiFScoreInvesting(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2012, 1, 1)
        self.SetEndDate(2021, 12, 31)
        self.SetCash(10000000)

        fscore_threshold = self.GetParameter("fscore_threshold", 7)

        self.UniverseSettings.Resolution = Resolution.Daily

        # Our universe is selected by Piotroski's F-Score
        self.AddUniverseSelection(FScoreUniverseSelectionModel(self, fscore_threshold))
        # Buy and hold the selected stocks
        self.AddAlpha(AlphaModel(InsightType.Price, InsightDirection.Up, timedelta(1)))
        # Equal-weighted portfolio
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())

    def OnSecuritiesChanged(self, changes):
        pass
