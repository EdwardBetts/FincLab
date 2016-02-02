""" Class : Logger

Author: Peter Lee
Date created: 2016 Jan 27

The Logger class makes use of the queue.Queue() to pass module logs into the queue pipe, and a listener (works on a different thread) to display logging information to the User Interface.

Handlers
--------
    console_handler : StreamHander()
        Directs outputs to sys.stdout; Using curses wrapper method, the logging outputs will be viewable when quiting the UI.

    ui_handler : QueueHandler()
        Directs outputs to the queue.Queue() object (same queue within the FincLab engine).

"""


import queue
import logging
import logging.handlers
from config import config


class FincLabQueueHandler(logging.handlers.QueueHandler):
    """
    Add .type='log' to the default attributes
    """

    def __init__(self, queue):
        """
        Initialise the FincLabQueueHandler.

        Parameters
        ----------
            queue : queue.Queue()
                A passed queue
        """
        logging.handlers.QueueHandler.__init__(self, queue)

    def prepare(self, record):
        """
        Override the default method to include an additional attribute .type
        # The format operation gets traceback text into record.exc_text
        # (if there's exception data), and also puts the message into
        # record.message. We can then use this to replace the original
        # msg + args, as these might be unpickleable. We also zap the
        # exc_info attribute, as it's no longer needed and, if not None,
        # will typically not be pickleable.
        """
        self.format(record)
        record.msg = record.message
        record.args = None
        record.exc_info = None
        record.type = 'LOG'
        return record


def create_logger(event_queue):
    """
    Create a logger with multiple handles.

    Parameters
    ----------
        event_queue : queue.Queue()
            The queue for the QueueHandler.
    """

    # Load settings
    level = logging.getLevelName(config['log']['level'])
    log_in_user_interface = config.getboolean('log', 'log_in_user_interface')
    save_to_file = config.getboolean('log', 'save_to_file')
    log_filename = config['log']['log_filename']

    # create a logger
    logger = logging.getLogger("FincLab")
    logger.setLevel(level)

    # Formatter
    formatter = logging.Formatter(fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    # create consoleHandler
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.DEBUG)
    # console_handler.setFormatter(formatter)
    # logger.addHandler(console_handler)

    # create queue handler for the user interface
    if log_in_user_interface:
        queue_handler = FincLabQueueHandler(event_queue)
        queue_handler.setLevel(level)
        queue_handler.setFormatter(formatter)
        logger.addHandler(queue_handler)

    # create a file handler to save log
    if save_to_file:
        file_handler = logging.FileHandler(log_filename, mode='w')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


if __name__ == '__main__':
    # Logging to a file
    # logging.basicConfig(filename='/Users/peter/Workspace/FincLab/src/example.log', level=logging.DEBUG)
    # logging.debug('This message should go to the log file.')
    # logging.info('So should this one')
    # logging.warning('And this too!')

    # Initialise the event_queue logger
    event_queue = queue.Queue()
    logger = create_logger(event_queue)

    # Testing the sys.stdout handler
    print("Testing the sys.stdout handler")
    logger.debug('Old: debug message')
    logger.info('Old: info msg')
    logger.warn('Old: warn msg')
    logger.error('Old: error msg')
    logger.critical('Old: critical msg')

    # Testing the queue handler
    print("Testing the queue handler")
    handler = logging.StreamHandler()
    listener = logging.handlers.QueueListener(event_queue, handler)
    listener.start()
    logger.warn('new: dwarn msg')
    logger.error('new: derror msg')
    logger.warn('new: warn msg')
    logger.error('new: error msg')
    logger.critical('new: critical msg')
    listener.stop()

    print("Tests complete.")
