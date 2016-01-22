"""
Class: Event-Driven Execution - Interactive Brokers

Author: Peter Lee
Last update: 2016-Jan-18

Sample module to hook up the event-driven system to a brokerage - a bit more sophisticated handling than directly tranform a OrderEvent to a FillEvent.

This module defines the IBExecutionHanlder, a class that talks to the Interative Brokers API and automate the execution.

The essential idea of the IBExecutionHandler class is to receive OrderEvent instances from the events queue, and then to execute them directly against the Interactive Brokers order API using the open source IbPy library.

The class will also handle the "Server Response" messages sent back via the API.

Note:
    The class itself could feasibly become rather complex, with execution optimisation logic as well as sophisticated error handling.

# IB API
The IB API utilises a message-based event system that allows this class to respond in particular ways to certain messages, in a similar manner to the event-driven backtester itself.

You may include some error handling via the _error_handler method.

The _reply_handler method is used to determine if a FillEvent instance needs to be created. The method asks if an "openOrder" message has been received, and checks whether an entry in the fill_dict for this particular orderID has already been set. If not, then one is created.

If _reply_handler method sees an "orderStatus" message, and that particular message states that an order has been filled, then it calls create_fill method to create a FillEvent. It also outputs the messge to the terminal for logging/debug purposes.

    This class forms the basis of an IB execution handler and can be used in place of the simulated execution handler, which is only suitable for backtesting. Before the IB handler can be utilised, however, it is necessary to create a live market feed handler to replace the historical data feed handler of the backtester system. In this way, we are reusing as much as possible from the backtest and live systems to ensure that code "swap out" is minimised and thus behaviour across both is similar, if not identical.
"""

import datetime as dt
import time

from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message

from event import FillEvent, OrderEvent
from execution import ExecutionHandler


class IBExecutionHandler(ExecutionHandler):
    """
    Handles order exectuion via the Interactive Brokers API, for use against accounts when trading live directly.

    Notes:
        Specification of "order_routing" is defaulted to "SMART".
        "currenty" is set to "US Dollars".
    """

    def __init__(self, events, order_routing="SMART", currency="USD"):
        self.events = events
        self.order_routing = order_routing
        self.currency = currency
        self.fill_dict = {}

        self.tws_conn = self.create_tws_connection()
        self.order_id = self.create_initial_order_id()
        self.register_handlers()

    def _error_handler(self, msg):
        """
        Handles the capturing of error messages.
        """
        # Currently no error handling.
        print("Server Error: {}".format(msg))

    def _reply_handler(self, msg):
        """
        Handles of server replies.
        """
        # Handle open order orderId processing
        if msg.typeName == "openOrder" and\
            msg.orderId == self.order_id and\
           not self.fill_dict.has_key(msg.orderId):
            self.create_fill_dict_entry(msg)

        # Handle Fills
        if msg.typeName == "orderStatus" and\
            msg.status == "Filled" and\
           self.fill_dict[msg.orderId]["filled"] == False:
            self.create_fill(msg)

        print("Server response: {}, {}\n".format(msg.typeName, msg))

    def create_tws_connection(self):
        """
        Connect to the Trader Workstation (TWS) running on the usual port of 7496, with a clientId of 10.
        The clientId is chosen by us and we will need to separate IDs for both the execution connection and market data connection, if the latter is used elsewhere.
        """
        tws_conn = ibConnection()
        # Perform connection.
        tws_conn.connect()
        return tws_conn

    def create_initial_order_id(self):
        """
        Create the initial order ID used for Interactive Brokers to keep track of submitted orders.

        Note:
            A more sophisticated approach would be query IB for the latest available ID and use that.

            You can always reset the current API order ID via the Trader Workstation > Global Configuration > API Settings panel.
        """
        # WARNING: Use "1" as a "quick go" solution
        return 1

    def register_handlers(self):
        """
        Register the error and server replay messge handling functions.
        """
        # Assign the error handling function defined above to the TWS connection
        self.tws_conn.register(self._error_handler, 'Error')

        # Assign all of the server reply messages to the reply_handler function
        self.tws_conn.registerAll(self._reply_handler)

    def create_contract(self, symbol, sec_type, exch, prim_exch, curr):
        """
        Create a Contract object defining what will be purchased, at which exchange and in which currency.

        Parameters:
            symbol - The ticker symbol for the contract
            sec_type - The security type for the contract ("STK" is "stock")
            exch - The exchange to carry out the contract on
            prim_exch - The primary exchange to carry out the contract on
            curr - The currency in which to purchase the contract
        """
        contract = Contract()
        contract.m_symbol = symbol
        contract.m_secType = sec_type
        contract.m_exchange = exch
        contract.m_primaryExch = prim_exch
        contract.m_currency = curr
        return contract

    def create_order(self, order_type, quantity, action):
        """
        Create an Order object (Market/Limit) to go long/short.

        Parameters:
            order_type = "MKT", "LMT" for Market or Limit orders
            quantity - Integral number of assets to order
            action - "BUY" or "SELL"

        Note:
            This method generates the second component of the Contract/Order pair. It expects an order type (e.g., market or limit), a quantity to trade and an "action" (buy or sell).
        """
        order = Order()
        order.m_orderType = order_type
        order.m_totalQuantity = quantity
        order.m_action = action
        return order

    def create_fill_dict_entry(self, msg):
        """
        Creates an entry in the Fill Dictionary that lists orderIds and provides security information.

        This is needed for the event-driven behaviour of the IB server message behaviour.

        Note:
            In order to avoid duplicating FillEvent instances for a particular order ID, the dictionary "fill_dict" is used to store keys that match particular order IDs.

            When a fill has been generated, the "filled" key of an entry for a particular order ID is set to True. If a subsequent "Server Response" message is received from IB stating that an order has been filled (and is a duplicate message), it will not lead to a new fill.
        """
        self.fill_dict[msg.orderId] = {
            "symbol": msg.contract.m_symbol,
            "exchange": msg.contract.m_exchange,
            "direction": msg.order.m_action,
            "filled": False
        }

    def create_fill(self, msg):
        """
        Handles the creation of the "FillEvent" that will be placed onto the events queue subsequent to an order being filled.
        """
        fd = self.fill_dict[msg.orderId]

        # Prepare the fill data
        symbol = fd["symbol"]
        exchange = fd["exchange"]
        filled = msg.filled
        direction = fd['direction']
        fill_cost = msg.avgFillPrice

        # Create a fill event object
        fill_event = FillEvent(
            dt.datetime.utcnow(),
            symbol,
            exchange,
            filled,
            direction,
            fill_cost
        )

        # Make sure that multiple messages don't create additional fills
        self.fill_dict[msg.orderId]["filled"] = True

        # Place the fill event onto the event queue
        self.events.put(fill_event)

    def execute_order(self, event):
        """
        Creates the necessary InteractiveBrokers order object and submits it to IB via their API.

        The results are then queried in order to generaete a corresponding Fill object, which is placed back on the event queue.

        Parameters:
            event - Contains an Event object with order information.

        Note:
            To override the "execute_order" method from the ExecutionHandler abtract base class. This method actually carries out the order placement with the IB API.

            We first check that the event being received to this method is actually an OrderEvent, and then prepare the Contract and Order objects with their respective parameters.

            Once both are created, the IbPy method .placeOrder() of the connection object is called with an associated order_id.

            Finally, we increment the orderID to ensure we don't duplicate orders.

            It is **extremely important** to call the time.sleep(1) method to ensure the order actually goes through to IB. Removal of this line leads to inconsistent behaviour of the API.
        """

        if event.type == 'order':
            # Prepare the parameters for the asset order
            asset = event.symbol
            asset_type = "STK"
            order_type = event.order_type
            quantity = event.quantity
            direction = event.direction

            # Create the Interactive Brokers contract via the passed Order event
            ib_contract = self.create_contract(
                symbol=asset,
                sec_type=asset_type,
                exch=self.order_routing,
                prim_exch=self.order_routing,
                curr=self.currency
            )

            # Create the Interactive Brokers order via the passed Order event
            ib_order = self.create_order(
                order_type=order_type,
                quantity=quantity,
                action=direction
            )

            # Use the connection to send the order to IB
            self.tws_conn.placeOrder(
                self.order_id, ib_contract, ib_order
            )

            # Note: This following line is CRUCIAL - to ensure the order goes through!
            time.sleep(1)

            # Increment the order ID for this session
            self.order_id += 1
