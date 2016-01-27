"""
Class: Event-Driven Engine

Author: Peter Lee
Date created: 2016-Jan-19

Notes
-----
    The "Event-Driven Engine" is the core component of the system that:
        - Encapsulates the event-handling logic (by directing the events to appropriate components)
        - Manages events in a queue in a timely order, and
        - Process all events in the queue and sleeps for the period of "heartbeat" before waking up to process new events.

    The Engine object comprises of two while-loops:
        - The outer-loop (the "heartbeat" loop) : decides the speed of resolution of the system.
            * In a backtesting setting, the "heartbeat" rate is set to zero since all data points are historic and available. The backtesting ends if the DataHandler object lets the Engine ojbect know, by using a boolean .is_running attribute.
            * In a live trading setting, the "heartbeat" rate decides the resolution of the system, and is dependent upon the applied strategy. For example, a heart rate of 600 (seconds) means that the "Event Queue" is will query and queue up the MarketEvent every 10 minutes.
        - The inner-loop (the life cycle of an "Event") : Starting with receiving a MarketEvent, follow-up events are directly to corresponding components to be processed. As a result, the "Event Queue" is continually being populated and depopulated with events. The loop must be closed before a new MarketEvent can be processed.

Flow-Chart
----------

Main loop : The main process cycle of events.
    MarketEvent --> Strategy object (to calculate signal)
    --> SignalEvent --> Portfolio object (to transform into orders)
    --> (a set of) OrderEvent --> ExecutionHandler object (to simulate the execution in a backtesting or send to broker's API in live trading)
    --> FillEvent --> Portfolio object (to update positions given the fill orders)

Side loop : Some events are processed by multiple targets.
    MarketEvent --> Portfolio object (to reindex the time and update positions in the portfolio)

"""

import pprint  # "pretty-print" to display the stats in an output-friendly manner
import queue
import time
import datetime as dt


class Engine(object):
    """
    Core of the event-driven system : Sets up the event queue and directs event to the correct system component.
    """

    def __init__(self,
                 symbol_list,
                 data_handler,
                 execution_handler,
                 portfolio,
                 strategy,
                 event_queue=queue.Queue(),
                 heartbeat=0,
                 initial_capital=1000000,
                 start_date=dt.datetime(1990, 1, 1, 0, 0, 0)):
        """
        Initialises the Engine object.

        Parameters
        ----------
        data_folder : string, default "~/Work/FinanceData/Stock/US/"
            The full path to the data directory. Supports .csv, .xls, .xlsx and .dta formats.
        symbol_list : list of strings
            Each string in the list is the symbol (ticker) for the financial asset.
        initial_capital : int, default 1000000
            The openning balance for the portfolio. The currency is assumed to be identical to that of price quote of the underlying asset.
        heartbeat : int (seconds), default 0
            The duration of heartbeat in seconds. Heartbeat is the period the engine hibernates before it checks for market updates.
        start_date : datetime(), default datetime.datetime(1990,1,1,0,0,0) (1990-Jan-1)
            The start datetime since when the strategy begins to evaluate.
        data_handler : DataHandler (class) or an inherited class, default HistoricCSVDataHandler
            Handles the market data feed.
        execution_handler : ExecutionHandler (Class) or an inherited class, default SimulatedExecutionHandler
            Handles the orders, and fills for trades.
        portfolio : Portfolio (Class) or an inherited class, default Portfolio.
            Keeps track of portfolio current and prior positions.
        event_queue : queue.Queue()
            Queue to queue up different events
        strategy : Strategy (Class) or an inherited class, default MovingAverageCrossoverStrategy.
            Generates signals based on market data.
        """

        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy

        self.event_queue = event_queue

        self.num_signals = 0  # Number of processed SignalEvents
        self.num_orders = 0  # Number of processed OrderEvents
        self.num_fills = 0  # Number of process FillEvents
        self.num_strats = 1  # Number of strategies

        # Attach system components to internal members
        self._initialise_system_components()

    def _initialise_system_components(self):
        """
        Attaches the trading objects (DataHandler, Strategy, Portfolio and ExecutionHandler) to internal members.
        """

        print("Creating DataHandler, Strategy, Portfolio and ExecutionHandler.")

        self.data_handler = self.data_handler_cls(
            event_queue=self.event_queue,
            symbol_list=self.symbol_list
        )

        self.strategy = self.strategy_cls(
            bars=self.data_handler,
            event_queue=self.event_queue
        )

        self.portfolio = self.portfolio_cls(
            bars=self.data_handler,
            event_queue=self.event_queue,
            start_date=self.start_date,
            initial_capital=self.initial_capital
        )

        self.execution_handler = self.execution_handler_cls(
            event_queue=self.event_queue
        )

    def _run_engine(self):
        """
        Using two while-loops to execute the event-driven engine.
        The engine is single treaded, and all events are placed in a FIFO queue.

        Notes
        -----
        The core of the engine comprises of two while-loops:
            - The outer keeps track of the heartbeat of the system.
            - The inner checks if there is an event in the Queue object, and acts on it.

       Flow-Chart
       ----------

       1) Main flow: The main process cycle of events.
       MarketEvent --> Strategy object (to calculate signal)
       --> SignalEvent --> Portfolio object (to transform into orders)
       --> (a set of) OrderEvent --> ExecutionHandler object (to simulate the execution in a backtesting or send to broker's API in live trading)
       --> FillEvent --> Portfolio object (to update positions given the fill orders)

        2) Side loop : Some events are processed by multiple targets.
        MarketEvent --> Portfolio object (to reindex the time and update positions in the portfolio)
        """
        i = 0
        while True:
            i += 1
            print(i)
            # Check if DataHandler is running --> if yes, get a mareket update
            if self.data_handler.is_running:
                self.data_handler.update_bars()  # push latest bar and put a market event into the queue
            else:
                break  # request to "QUIT" from DataHandler

            # To process all remaining events following this MarketEvent
            while True:
                try:
                    event = self.event_queue.get(block=False, timeout=None)
                except queue.Empty:
                    break  # End of queue --> get more data
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            # print("Received a market event at {}".format(event.datetime))
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                        elif event.type == 'SIGNAL':
                            self.num_signals += 1
                            self.portfolio.update_signal(event)
                        elif event.type == 'ORDER':
                            self.num_orders += 1
                            self.execution_handler.execute_order(event)
                        elif event.type == 'FILL':
                            self.num_fills += 1
                            self.portfolio.update_fill(event)
        time.sleep(self.heartbeat)

    def _output_performance(self):
        """
        Outputs the strategy performance from the engine.

        Notes
        -----
        The performance of the strategy can be displayed to the terminal/console.
        The equity curve pandas DataFrame is created and the summary statistics are displayed, as well as the count of Signals, Orders and Fills.
        """
        self.portfolio.create_equity_curve_dataframe()

        print("Creating summary statistics...")
        stats = self.portfolio.output_summary_stats()

        print("Creating equity curve...")
        print(self.portfolio.equity_curve.tail(10))
        pprint.pprint(stats)

        print("Number of Signals: {}".format(self.num_signals))
        print("Number of Orders: {}".format(self.num_orders))
        print("Number of Fills: {}".format(self.num_fills))

    def run(self):
        """
        Starts the event-driven system.
        """
        self._run_engine()
        self._output_performance()


if __name__ == '__main__':
    import sys

    def progress_bar(end_val, bar_length=50):
        for i in range(0, end_val):
            percent = float(i + 1) / end_val
            hashes = '#' * int(round(percent * bar_length))
            spaces = ' ' * (bar_length - len(hashes))
            sys.stdout.write("\rbacktest: [{0}] {1}%".format(hashes + spaces, int(round(percent * 100))))
            time.sleep(0.1)
            sys.stdout.flush()

    progress_bar(100)
