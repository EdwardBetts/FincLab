import pandas as pd

from event import OrderEvent
from performance import create_sharpe_ratio, create_drawdowns

"""
Class : Portfolio
-----------------
A "first go" Portfolio object when testing out new strategies. Other Portfolios can be derived from it and override sections to add more complexity.

The Portfolio object must be able to handle SignalEvent objects, generate OrderEvent objects and interpret FillEvent objects to update positions.

Attributes
----------
current_positions : dict
    Stores the current positions for the last market bar update, for each symbol.

all_positions : list of dict
    Stores a list of all previous positions recorded at the timestamp of a MarketEvent. Negative positions mean the asset has been shorted.

current_holdings : dict
    Stores the most up to date dictionary of all symbol holdings values, plus a few more accounts

all_holdings : list of dict
    Stores all historical symbol holdings, plus a few more accounts

Methods
-------
update_timeindex() : handles the new holdings tracking.
    It firstly obtains the latest prices from the market data handler, and creates a new dictionary of symbols to represent the current positions, by setting the "new" positions equal to the "current" positions. The current positions are only modified when a FillEvent is received.

Assumptions
-----------
A predetermined fixed quantity size per order, inrrespective of cash held.
Does not handle position sizing.
"""


class Portfolio(object):
    """
    The Portfolio class handles the positions and market value of all instruments at a resolution of a "bar", i.e., secondly, minutely, 5-min, 30-min or EOD.

    The initialisation of the Portfolio object requires access to the bars DataHandler, the events Event Queue, a start datetime stamp and an initial capital value (defaulting to $100,000).

    The positions DataFrame stores a time-index of the quantity of positions held.

    The holdings DataFrame stores the cash and total market holdings value of each symbol for a particular time-index, as well as the percentage change in portfolio total across bars.
    """

    def __init__(self, bars, event_queue, start_date, initial_capital=1000000.0):
        """
        Initialises the portfolio with bars, an event queue,  a starting datetime index and initial capital (USD unless otherwise stated).

        Parameters
        ----------
        bars : The DataHandler object with current market data
        event_queue : The Event Queue object
        start_date : datetime.datetime()
            The start date (bar) of the portfolio
        initial_capital : float, default 1,000,000
            The starting capital in dollars
        """

        self.bars = bars
        self.event_queue = event_queue
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital

        # Construct all_positions
        self.all_positions = self.construct_all_positions()
        # The following creates a dictionary for each symbol, sets the value to zero for each, using a dictionary comprehension.
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

        It is similar to .construct_all_positions() method, but adds extra keys for:
            - cash
            - commission
            - total: represent respectively the spare cash in the account after any purchases
            - cumulative commission accrued
            - the total account equity including cash and any open positions.

        Notes
        -----
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
        """
        d = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        d['cash'] = self.initial_capital
        d['commission'] = 0
        d['total'] = self.initial_capital
        return d

    def update_timeindex(self, event):
        """
        Adds a new record to the positions matrix for the current market data bar. Makes use of a MarketEvent from the events queue.
        """
        latest_datetime = self.bars.get_latest_bar_datetime(
            self.symbol_list[0]
        )

        # Update positions
        # ================
        dp = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])
        dp['datetime'] = latest_datetime

        for s in self.symbol_list:
            dp[s] = self.current_positions[s]  # self.current_positions is modified when receiving a FillEvent

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
            market_value = self.current_positions[s] * self.bars.get_latest_bar_value(s, "adj_close")
            dh[s] = market_value
            dh['total'] += market_value

        # Append the current holdings
        self.all_holdings.append(dh)

    def update_positions_from_fill(self, fill_event):
        """
        Takes a Fill object and updates the position matrix to reflect the new position.

        This method first determines whether a FillEvent is a Buy or a Sell and then updates the current_positions dictionary accordingly by adding/subtracting the correct quantity of shares.

        Parameters
        ----------
        fill_event : FillEvent
            The Fill object to update the position with
        """

        # Check whether the fill is a buy or a sell
        fill_dir = 0
        if fill_event.direction == 'BUY':
            fill_dir = 1
        if fill_event.direction == 'SELL':
            fill_dir = -1

        # Update positions list with new quantities
        self.current_positions[fill_event.symbol] += fill_dir * fill_event.quantity

    def update_holdings_from_fill(self, fill_event):
        """
        Takes a Fill object and updates the holdings matrix to reflect the holdings value.

        Parameters
        ----------
        fill_event : FillEvent object
            The Fill object to update the holdings with.

        Notes
        -----
        update_holdings_from_fill is similar to update_positions_from_fill, except that update holdings does not use the cost associated from the FillEvent. The rationale is that in a backtesting environment, the fill cost is actually unknown (i.e., the market impact and the depth of book are unknown).

        Thus the fill cost is set to the "current market price", which is the closing price of the last bar. The holdings for a particular symbol are then set to be equal to the fill cost multiplied by the transacted quantity. For most lower frequency trading strategies in liquid markets, this is a reasonable approximation, but at high frequency these issues will need to be considered in a production backtest and live trading engine.
        """
        # Check whether the fill is a buy or a sell
        fill_dir = 0
        if fill_event.direction == 'BUY':
            fill_dir = 1
        if fill_event.direction == 'SELL':
            fill_dir = -1

        # Update holdings list with new quantities
        fill_cost = self.bars.get_latest_bar_value(fill_event.symbol, "adj_close")
        cost = fill_dir * fill_cost * fill_event.quantity

        self.current_holdings[fill_event.symbol] += cost
        self.current_holdings['commission'] += fill_event.commission
        self.current_holdings['cash'] -= (cost + fill_event.commission)
        self.current_holdings['total'] -= (cost + fill_event.commission)

    def update_fill(self, event):
        """
        Updates the portfolio current positions and holdings from a FillEvent
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)

    def generate_native_order(self, signal_event):
        """
        Simply creates an Order object as a constant quantity sizing of the signal object, without risk management or position sizing considerations.

        The method handles longing, shorting and exiting of a position, based on the current quantity and particular symbol. Corresponding *OrderEvent* obejcts are then generated.

        Parameters
        ----------
        signal_event : The SignalEvent object

        Notes
        -----
        This method simply takes a signal to go long or short an asset, sending an order to do so for 100 shares of such an asset. Clearly 100 is an arbitrary value, and will cearly depend upon the portfolio total equity in a production simulation.

        In a realistic implementation, this value will be determined by a risk management or position sizing overlay.
        """
        order_event = None

        symbol = signal_event.symbol
        direction = signal_event.signal_type
        strength = signal_event.strength

        mkt_quantity = 100 * strength
        cur_quantity = self.current_positions[symbol]
        order_type = "MKT"

        if direction == 'LONG' and cur_quantity == 0:
            order_event = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT' and cur_quantity == 0:
            order_event = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')

        if direction == 'EXIT' and cur_quantity > 0:
            order_event = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        if direction == 'EXIT' and cur_quantity < 0:
            order_event = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')

        return order_event

    def update_signal(self, event):
        """
        Acts on a SignalEvent to generate new orders based on the portfolio logic.

        It simply calls the "Native" order method and adds the generated order to the events queue.
        """
        if event.type == "SIGNAL":
            order_event = self.generate_native_order(event)
            self.event_queue.put(order_event)

    def create_equity_curve_dataframe(self):
        """
        Creates a pandas DataFrame from the all_holdings list of dictionaries.

        This method simply creates a cumulative returns series, useful for performance calculations, and then normalises the equity curve to be percentaged based. Thus the account initial size is equal to 1.0.
        """
        df_curve = pd.DataFrame(self.all_holdings)
        df_curve.set_index('datetime', inplace=True)
        df_curve['returns'] = df_curve['total'].pct_change()
        df_curve['equity_curve'] = (1.0 + df_curve['returns']).cumprod()
        self.equity_curve = df_curve

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

        stats = [("Total Return: {:.2f}%".format((total_return - 1) * 100)),
                 ("Sharpe Ratio: {:.2f} ".format(sharpe_ratio)),
                 ("Max Drawdown: {:.2f}%".format(max_dd * 100)),
                 ("Drawdown Duration: {:.2f}".format(dd_duration))]
        # self.equity_curve.to_csv("equity.csv")
        return stats

if __name__ == '__main__':
    print('Debugging...')

