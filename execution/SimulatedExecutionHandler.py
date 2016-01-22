import datetime as dt
from event import FillEvent
from execution.ABC import ABC as ExecutionABC


class SimulatedExecutionHandler(ExecutionABC):
    """
    The simulated execution handler simply converts all order objects into their equivalent fill objects automatically without latency, slippage or fill-ratio issues.

    This allows a straightforward "first go" test of any strategy, before implementation with a more sophisticated execution handler.

    Parameters
    ----------
    event_queue : queue.Queue()
        The event queue.
    """

    def __init__(self, event_queue):
        """
        Initiates the handler, setting the event queues up internally.

        Parameters:
            event_queue - the queue of Event objects
        """
        self.event_queue = event_queue

    def execute_order(self, event):
        """
        Simply converts Order objects into Fill objects naitvely, i.e., without any latency, slippage or fill ratio problems.

        Parameters:
            event - Contains an Event object with order information.
        """
        if event.type == 'ORDER':
            fill_event = FillEvent(
                timeindex=dt.datetime.utcnow(),
                symbol=event.symbol,
                exchange='N/A',
                quantity=event.quantity,
                direction=event.direction,
                fill_cost=None,
                commission=None
            )
            self.event_queue.put(fill_event)

