"""
Class: Event Class

Event : The Event class is outlines the object to be placed in the event queue in the event-driven system.

Types of Events (Inherited Event Classes)
-----------------------------------------
MarketEvent : Occurs when the DataHandler objet receives a new update of market data. In a backtest setting using historical data, the MarketEvent is generated sequentially while sequentially loading data bars.
    The MarketEvent will be received by the Strategy object (to generate new trading signals), and by the Portfolio object (to update position information).

SignalEvent : Contains a strategy ID, a ticker symbol, a timestamp for when it was generated, a direction (long or short) and a "strength" indicator (this is useful for mean reversion strategies). The SignalEvents are utilised by the Portfolio object as advice for how to trade.

OrderEvent : When a Portfolio object receives SignalEvents, it assesses them in the wider context of the portfolio, in terms of risk and position sizing. This ultimately leads to OderEvents that will be sent to an ExecutionHandler. The OderEvent is slightly more complex than a SignalEvent since it contains a quantity field in addition to the properties of SignalEvent. The quantity is determined by the Portfolio constraints. In addition, the OrderEvent has a print_order() method, used to output the information to console if necessary.

FillEvent : When an ExecutionHandler receives an OrderEvent, it must transact the order. Once an order has been transacted, it generates a FillEvent, which describes the cost of purchase or sale as well as the transaction costs, such as fees or slippage. It contains a timestamp for when an order was filled, the symbol of the order and the exchange it was executed on, the quantity of shares transacted, the actual price of the purchase and the commission incurred. The FillEvent will be received by the Portfolio object and positions will be updated.
"""


class Event(object):
    """
    Event is the base class providing an interface for all inherited events, which will trigger further events in the backtesting engine.
    """
    pass


class MarketEvent(Event):
    """
    Handles the event of receiving a new market update with corresponding bars.
    """

    def __init__(self, date_time):
        """
        Initialises the MarketEvent.

        Parameters
        ----------
        date_time : datetime.datetime()
            The datetime object of the last bar.
        """
        self.type = 'MARKET'
        self.datetime = date_time


class SignalEvent(Event):
    """
    Handles the event of sending a Signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    """

    def __init__(self, strategy_id, symbol, datetime, signal_type, strength=1):
        """
        Initialise the SignalEvent.

        Parameters
        ----------
        strategy_id : string
            The unique identifier for the Strategy object that generated the signal.
        symbol :string
            The ticker symbol (e.g., "GOOG")
        datetime : datetime.datetime()
            The timestamp at which the signal is generated.
        signal_type : either "LONG" or "SHORT"
            Either to go long or short.
        strength : float, default 1
            An optional model parameter to scale quantity at the portfolio level. Useful for pairs strategies.
        """

        self.type = 'SIGNAL'
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength


class OrderEvent(Event):
    """
    Handles the event of sending an Order to an execution system.
    """

    def __init__(self, symbol, order_type, quantity, direction):
        """
        Initialises the order type.

        Parameters
        ----------
        symbol : string
            The ticker of the asset to trade.
        order_type : string, either "MKT" or "LMT"
            "MKT" or "LMT" for Market or Limit
        quantity : int
            Non-negative integer for quantity
        direction : either "BUY" or "SELL"
            "BUY" or "SELL" for long or short
        """

        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type.upper()
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        """
        Outputs the values within the Order.
        """
        print("Order details: Symbol={symbol}, Type={type}, Quantity={quantity}, Direction={direction}".format(symbol=self.symbol, type=self.order_type, quantity=self.quantity, direction=self.direction))


class FillEvent(Event):
        """
        Stores the price, quantity and commission of an instrument actually filled. Encapsulates the notion of a Filled Order, as returned from a brokerage.

        Notes
        -----
        How are commissions calculated? The commission is currently calculated using the Interactive Brokers commisssions. For US API orders, this commission is 0.0035 USD minimum per order, with commissions capped at a 0.5% of the order value
        """

        def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, commission=None):
            """
            If commission is not provided, the Fill object will calculate it based on the trade size and Interactive Broker's fees.

            Parameters
            ----------
            timeidnex : datetime.datetime()
                The bar-resolution when the order was filled.
            symbol : string
                the ticker of the asset
            exchange : string
                The exchange where the order was filled
            quantity : int
                The filled quantity
            direction : string, either 'BUY' or 'SELL'
            fill_cost : float
                The dollar costs of filling the order (same currency as indicated in the price of the asset).
            commission - float, default to commission charges by Interactive Brokers
                (Optional) Commission
            """

            self.type = 'FILL'
            self.timeindex = timeindex
            self.symbol = symbol
            self.exchange = exchange
            self.quantity = quantity
            self.direction = direction
            self.fill_cost = fill_cost

            # calculate commission if necessary
            if commission is None:
                self.commission = self.calculate_ib_commission()
            else:
                self.commission = commission

        def calculate_ib_commission(self):
            """
            Calculates the fees of trading based on an Interactive Brokers fee structure for API, in dollars.

            This does not include exchange or ECN fees.

            Based on "US API Directed Orders":
            https://www.interactivebrokers.com/en/index.php? f=commission&p=stocks2
            """
            if self.fill_cost is not None:
                max_per_order = self.fill_cost * 0.005
                return max(0.0035 * self.quantity, max_per_order)
            else:
                return 0

if __name__ == '__main__':
    import sys
    import time

    def progress_bar(end_val, bar_length=50):
        for i in range(0, end_val):
            percent = float(i + 1) / end_val
            hashes = '#' * int(round(percent * bar_length))
            spaces = ' ' * (bar_length - len(hashes))
            sys.stdout.write("\rBacktest: [{0}] {1}%".format(hashes + spaces, int(round(percent * 100))))
            time.sleep(0.1)
            sys.stdout.flush()

    progress_bar(100)
