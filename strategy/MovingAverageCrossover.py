import datetime as dt
import numpy as np
from strategy.ABC import ABC as StrategyABC
from event import SignalEvent
import logging

"""
Strategy: Moving Average Crossover (MAC)
----------------------------------------

Data created: 2016-Jan-19

Moving Average Crossover (MAC) is extremely handy for testing a new backtesting implementation. On a daily timeframe, over a number of years, with long lookback periods, few signals are generated on a single stock and thus it is eay to manually verify that the system is behaving as would be expected.

The core of the strategy is the .calculate_signals() method. It reacts to a MarketEvent object and for each symbol traded obtains the latest N bar closing prices, where N is equal to the largest lookback period.

It then calculates both the short and long period simple moving averages. The rule of the strategy is to enter the market (go long a stock) when the short moving average value exceeds the long moving average value. Conversely, if the long moving average value exceeds the short moving average value, the stratgy is told to exit the market.

This logic is handled by placing a "SignalEvent" object on the events queue in each of the respective situations, and then updating the "bought" attribute (per symbol) to be "LONG" or "OUT", respectively. Since this is a long-only strategy, we won't be considering "SHORT" positions.
"""


class MovingAverageCrossover(StrategyABC):
    """
    Carries out a basic Moving Average Crossover strategy with a long/short simple weighted moving average. Default long/short window are 100/400 periods respectively - 100 and 400 as the "short" and "long" lookback periods for this strategy.

    The attribute "bought" is used to tell the Strategy when the backtest is actually "in the market". Entry signals are only generated if this is "OUT" and exit signals are only ever generated if this is "LONG" or "SHORT".
    """

    def __init__(self, bars, event_queue, short_window=100, long_window=400):
        """
        Initialises the Moving Average Crossover Strategy.

        Parameters
        ----------
        bars : the DataHandler object that provides bar information
        event_queue : The Event Queue object
        short_window : int
            The short moving average lookback
        long_window : int
            The long moving average lookback
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.event_queue = event_queue
        self.short_window = short_window
        self.long_window = long_window

        # Set to True if a symbol is in the market
        self.bought = self._initialise_bought()

        # Logger
        # self.logger = Logger("FincLab.strategy.MAC")
        self.logger = logging.getLogger("FincLab.mac")

        # Outputs description (Max 7 Lines)
        self.name = "Moving Average Cross-Over"
        self.description = """    Calculates moving average of 100- and 300-day windows for S&P 500 companies (a total of 505 stocks as of Jan 2016) and generates trading signals (long/short/exit).
        """

    def _initialise_bought(self):
        """
        Add keys to the bought dictionary for all symbols and sets them to "OUT" - the initial status, meaning out-of-the-market..
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought

    def calculate_signals(self, event):
        """
        Generates a new set of signals based on the MAC SMA with the short window crossing the long window, meaning a long entry and vice versa for a short entry.

        Parameters
        ----------
        event : Event object
            Acts upon receiving a MarketEvent
        """

        if event.type == "MARKET":
            for symbol in self.symbol_list:
                bars = self.bars.get_latest_bars_values(
                    symbol, "adj_close", periods=self.long_window
                )
                bar_date = self.bars.get_latest_bar_datetime(symbol)

                if bars is not None and bars != []:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])

                    dt_now = dt.datetime.utcnow()
                    signal_dir = ""

                    if short_sma > long_sma and self.bought[symbol] == "OUT":
                        self.logger.info("Long: {}".format(bar_date))
                        signal_dir = "LONG"
                        signal_event = SignalEvent(
                            strategy_id=1,
                            symbol=symbol,
                            datetime=dt_now,
                            signal_type=signal_dir,
                            strength=1.0
                        )
                        self.event_queue.put(signal_event)
                        self.bought[symbol] = 'LONG'
                    elif short_sma < long_sma and self.bought[symbol] == "LONG":
                        self.logger.info("SHORT: {}".format(bar_date))
                        signal_dir = "EXIT"
                        signal_event = SignalEvent(
                            strategy_id=1,
                            symbol=symbol,
                            datetime=dt_now,
                            signal_type=signal_dir,
                            strength=1.0
                        )
                        self.event_queue.put(signal_event)
                        self.bought[symbol] = "OUT"
