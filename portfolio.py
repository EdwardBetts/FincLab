"""
Portfolio Class

The Portfolio class is not an abstract base class (ABC) - instead it will be normal base class. This means that it can be instantiated and thus is useful as a "first go" Portfolio object when testing out new strategies. Other Portfolios can be derived from it and override sections to add more complexity.

The Porfolio is designed to handle position sizing and current holdings, but will carry out trading orders in a "dumb" manner by simply sending them directly to the brokerage with a predetermined fixed quantity size, irrespective of cash held. These are all unrealistic assumptions.

The portfolio contains the *all_positions* and *current_positions* members:
    all_positions - a dictionary; it stores a list of all previous positions recorded at the timestamp of a market data event. A position is simply the quantity of the asset held. Negative positions mean the asset has been shorted.
    current_positions - a dictionary that stores the current positions for the last market bar update, for each symbol.

And *holdings* members:
    all_holdings - it stores the historical list of all symbol holdings
    current_holdings - stores the most up to date dictionary of all symbol holdings values

The method *update_timeindex()* handles the new holdings tracking. It firstly obtains the latest prices from the market data handler, and creates a new dictionary of symbols to represent the current positions, by setting the "new" positions equal to the "current" positions.

The current positions are only modified when a *FillEvent* is obtained, which is handled later in the portfolio code. The method then appends this set of current positions to the all_positions list. The holdings are then updated in a similar manner, with the exception that the market value is recalculated by multiplying the current positions count with the closing price of the latest bar.

# Note
Continuing in the vein of the *Event* class hierachy, a *Portfolio* object must be able to hand *SignalEvent* objects, generate *OrderEvent* objects and interpret *FillEvent* objects to update positions. Thus, it is no surprise that the *Portfolio* objects are often the largest component of event-driven systems, in terms of lines of code (LOC).

# Genearte Order
While the Portfolio object
"""


import numpy as np
import pandas as pd
import datetime as dt
from math import floor  # To genearte integer-valued order sizes
try:
    import Queue as queue
except ImportError:
    import queue

from event import FillEvent, OrderEvent
from performance import create_sharpe_ratio, create_drawdowns


class Portfolio(object):
    """
    The Portfolio class handles the positions and market value of all instruments at a resolution of a "bar", i.e., secondly, minutely, 5-min, 30-min or EOD.

    The initialisation of the Portfolio object requires access to the bars DataHandler, the events Event Queue, a start datetime stamp and an initial capital value (defaulting to $100,000).

    The positions DataFrame stores a time-index of the quantity of positions held.

    The holdings DataFrame stores the cash and total market holdings value of each symbol for a particular time-index, as well as the percentage change in portfolio total across bars.
    """

    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        """
        Initialises the portfolio with bars and an event queue.
        Also includes a starting datetime index and initial capital (USD unless otherwise stated).

        Parameters:
            bars - The DataHandler object with current market data
            events - The Event Queue object
            start_date - The start date (bar) of the portfolio
            initial_capital - The starting capital in dollars
        """

        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital

        # Construct all_positions
        self.all_positions = self.construct_all_positions()
        # The following simply creates a dictionary for each symbol, sets the value to zero for each, using a dictionary comprehension.
        self.current_positions = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])

        # Construct all_holdings
        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def construct_all_positions(self):
        """
        Constructs the positions list using the start_date to determine when the time index will begin.
        """
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        d['datetime'] = self.start_date

        # Add the dictionary to a list
        return [d]

    def construct_all_holdings(self):
        """
        Constructs the holdings list using the start_date to determine when the time index will begin.

        It is similar to .construct_all_positins() method, but adds extra keys for:
            - cash
            - commission
            - total: represent respectively the spare cash in the account after any purchases
            - cumulative commission accrued
            - the total account equity including cash and any open positions.

        Note:
            Short positions are treated as negative.
            The starting cash and total account equity are both set to the initial capital.

        In this manner, there are separate "accounts" for each symbol, the "cash on hand", the "commission" paid, and a "total" portfolio value. Clearly this does not take into account margin requirements or shorting constraints.
        """
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0
        d['total'] = self.initial_capital

        # return a list
        return [d]

    def construct_current_holdings(self):
        """
        This constructs the dictionary which will hold the instantaneous value of the portfolio across all symbols.

        It does not wrap the dictionary in a list, because it is only creating a single entry.
        """
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event):
        """
        Adds a new record to the positions matrix for the current market data bar. This reflects the PREVIOUS bar, i.e., all current market data at this stage is known (OHLCV).

        Makes use of a MarketEvent from the events queue.
        """
        latest_datetime = self.bars.get_latest_bar_datetime(
            self.symbol_list[0]
        )

        # Update positions
        # ================
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['datetime'] = lastest_datetime

        for s in self.symbol_list:
            dp[s] = self.current_positions[s]

        # Append the current positions
        self.all_positions.append(dp)

        # Update holdings
        # ===============
        dh = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            # Approximation to the real value
            market_value = self.current_positions[s] * self.bars.get_latest_bar_values(s, "adj_close")
            dh[s] = market_value
            dh['total'] += market_value

        # Append the current holdings
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill):
        """
        Takes a Fill object and updates the position matrix to reflect the new position.

        Parameters:
            fill - The Fill object to update the position with

        Note:
            This method determines whether a *FillEvent* is a Buy or a Sell and then updates the current_positions dictionary accordingly by adding/subtracting the correct quantity of shares.
        """

        # Check whether the fill is a buy or a sell
        fill_dir = 0
        if fill.direction = 'buy':
            fill_dir = 1
        if fill.direction = 'sell':
            fill_dir = -1

        # Update positions list with new quantities
        self.current_positions[fill.symbol] += fill_dir*fill.quantity

    def update_holdings_from_fill(self, fill):
        """
        Takes a Fill object and updates the holdings matrix to reflect the holdings value.

        Parameters:
            fill - The Fill object to update the holdings with.

        Note:
            update_holdings_from_fill is similar to update_positions_from_fill, except that update holdings does not use the cost associated from the FillEvent. The rationale is that in a backtesting environment, the fill cost is actually unknown (i.e., the market impact and the depth of book are unknown).
            Thus the fill cost is set to the "current market price", which is the closing price of the last bar. The holdings for a particular symbol are then set to be equal to the fill cost multiplied by the transacted quantity. For most lower frequency trading strategies in liquid markets, this is a reasonable approximation, but at high frequency these issues will need to be considered in a production backtest and live trading engine.
        """
        # Check whether the fill is a buy or a sell
        fill_dir = 0
        if fill.direction = 'buy':
            fill_dir = 1
        if fill.direction = 'sell':
            fill_dir = -1

        # Update holdings list with new quantities
        fill_cost = self.bars.get_latest_bar_value(fill.symbol, "adj_close")
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings from a FillEvent
        """
        if event.type == 'fill':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_native_order(self, signal):
        """
        Simply creates an Order object as a constant quantity sizing of the signal object, without risk management or position sizing considerations.

        Parameters:
            signal - The tuple containing Signal information

        Notes:
            This method simply takes a signal to go long or short an asset, sending an order to do so for 100 shares of such an asset. Clearly 100 is an arbitrary value, and will cearly depend upon the portfolio total equity in a production simulation.

            In a realistic implementation, this value will be determined by a risk management or position sizing overlay.

            The method handles longing, shorting and existing of a position, based on the current quantity and particular symbol. Corresponding *OrderEvent* obejcts are then generated.
        """
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength

        mkt_quantity = 100
        cur_quantity = self.current_positions[symbol]
        order_type = "mkt"

        if direction == 'long' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'buy')
        if direction == 'short' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'sell')

        if direction == 'exit' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'sell')
        if direction == 'exit' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'buy')

        return order

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders based on the portfolio logic.

        It simply calls the "Native" order method and adds the generated order to the events queue.
        """
        if event.type == "signal":
            order_event = self.generate_native_order(event)
            self.events.put(order_event)

    def create_equity_curve_dataframe(self):
        """
        Creates a pandas DataFrame from the all_holdings list of dictionaries.

        This method simply creates a returns stream, useful for performance calculations, and then normalises the equity curve to be percentaged based. Thus the account initial size is equal to 1.0.
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve[total].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        self.equity_curve = curve

    def output_summary_stats(self):
        """
        Creates a list of summary statistics for the portfolio.
        """
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns, periods=252)
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown

        stats = [("Total Return: {:2d}%".format((total_return - 1) * 100)),
                 ("Sharpe Ratio: {:2d}".format(sharpe_ratio)),
                 ("Max Drawdown: {:2d}%".format(max_dd * 100)),
                 ("Drawdown Duration: {:2d}".format(dd_duration))]
        self.equity_curve.to_csv("equity.csv")
        return stats
