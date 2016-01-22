""" FincLab """

import datetime as dt
from portfolio import Portfolio
from engine import Engine
exec("from data.{module} import {module} as DataHandler".format(module="HistoricDataHandler"))
exec("from execution.{module} import {module} as ExecutionHandler".format(module="SimulatedExecutionHandler"))
exec("from strategy.{module} import {module} as Strategy".format(module="MovingAverageCrossover"))


def main():
    # Program parameters
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = dt.datetime(2014, 1, 1, 0, 0, 0)
    symbol_list = ['AAPL']

    # Backtest
    engine = Engine(
        symbol_list=symbol_list,
        data_handler=DataHandler,
        execution_handler=ExecutionHandler,
        portfolio=Portfolio,
        strategy=Strategy,
        heartbeat=heartbeat,
        initial_capital=initial_capital,
        start_date=start_date
    )
    engine.run()

if __name__ == "__main__":
    main()
