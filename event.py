"""
Class: Events Class (a component of the event-driven backtester)

4 components of event-driven system:

    1. Event: The *Event* is the fundamental class unit of the event-driven system. The events are generated and stored in a queue - and processed throughout the event loop. There are four basic types of the events:
        - "market": MarketEvents are triggered when the outer while loop of the backtesting system begins a new "heartbeat". It occurs when the DataHandler object receives a new update of market data or any symbols which are currently being tracked. It is used to trigger the *Strategy* object generating new trading signals. The event object simply contains an identification that it is a market event, with no other structure.
        - "signal": The *Strategy* object utilises market data to create new SignalEvent. The SignalEvent contains a strategy ID, a ticker symbol, a timestamp for when it was generated, a direction (long or short) and a "strength" indicator (this is useful for mean reversion strategies). The SignalEvents are utilised by the Portfolio object as advice for how to trade.
        - "order": When a Portfolio object receives SignalEvents, it assesses them in the wider context of the portfolio, in terms of risk and position sizing. This ultimately leads to OderEvents that will be sent to an ExecutionHandler. The OderEvent is slightly more complex than a SignalEvent since it contains a quantity field in addition to the properties of SignalEvent. The quantity is determined by the Portfolio constraints. In addition, the OrderEvent has a print_order() method, used to output the information to console if necessary.
        - "fill": When an ExecutionHandler receives an OrderEvent, it must transact the order. Once an order has been transacted, it generates a FillEvent, which describes the cost of purchase or sale as well as the transaction costs, such as fees or slippage. It contains a timestamp for when an order was filled, the symbol of the order and the exchange it was executed on, the quantity of shares transacted, the actual price of the purchase and the commission incurred.
    2. Event Queue
    3. DataHandler
    4. Strategy
    5. Portfolio
    6. ExecutionHandler
    7. Backtest
"""


class Event(object):
    """
    Event is the base class providing an interface for all inherited events, that will trigger further events in the backtesting engine.
    """
    pass


class MarketEvent(Event):
    """
    Handles the event of receiving a new market update with corresponding bars.
    """

    def __init__(self):
        self.type = 'market'


class SignalEvent(Event):
    """
    Handles the event of sending a Signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    """

    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        """
        Initialise the SignalEvent.

        Parameters:
            strategy_id - The unique identifier for the strategy that generated the signal.
            symbol - The ticker symbol (e.g., "GOOG")
            datetime - The timestamp at which the signal is generated.
            signal_type - "long" or "short"
            strength - An adjustment factor "suggestion" used to scale quantity at the portfolio level. Useful for pairs strategies.
        """

        self.type = 'signal'
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength


class OrderEvent(Event):
    """
    Handles the event of sending an Order to an execution system.
    The order contains a symbol (e.g. "GOOG"), a type ("market" or "limit"), quantity and a direction
    """

    def __init__(self, symbol, order_type, quantity, direction):
        """
        Initialises the order type, setting whether it is a Market order ("market") or Limit order ("limit"), has a quantity (integer) and its direction ("buy" or "sell").

        Parameters:
            symbol - The asset to trade
            order_type - "market" or "limit" for Market or Limit
            quantity - Non-negative integer for quantity
            direction - "buy" or "sell" for long or short
        """

        self.type = 'order'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        """
        Outputs the values within the Order.
        """
        print("Order details: Symbol={symbol}, Type={type}, Quantity={quantity}, Direction={direction}".format(symbol=self.symbol, type=self.order_type, quantity=self.quantity, direction=self.direction))


class FillEvent(Event):
        """
        Encapsulates the notion of a Filled Order, as returned from a brokerage. Stores the quantity of an instrument actually filled and at what price. In addition, stores the commission of the trade from the brokerage.

        Note - How are commissions calculated?
        The commission is currently calculated using the Interactive Brokers commisssions. For US API orders, this commission is 0.0035 USD minimum per order, with commissions capped at a 0.5% of the order value
        """

        def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, commission=None):
            """
            If commission is not provided, the Fill object will calculate it based on the trade size and Interactive Broker's fees.

            Parameters:
                timeidnex - The bar-resolution when the order was filled.
                symbol - the ticker of the asset
                exchange - The exchange where the order was filled
                quantity - The filled quantity
                direction - either 'buy' or 'sell'
                fill_cost - The holding values in dollars
                commission - An optional commission sent from Interactive Broker
            """

            self.type = 'fill'
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
            max_per_order = self.fill_cost * 0.005
            return max(0.0035 * self.quantity, max_per_order)
