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


class Logger(logging.Logger):
    """
    Base class for the logger object.

    """
    def __init__(self,
                 logger_name='FincLab',
                 logfile=None,
                 event_queue=None,
                 level=logging.DEBUG
                 ):
        """
        Initialises the FincLabLogger.

        Parameters
        ----------
            logger_name : string
                The name of the logger.
            logfile : string, default None
                A logfile will be created given a name.
            event_queue : queue.Queue(), default None
                The queue to store all logs and other events.
            level : logging.XXXX (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                the minimum level to be reported.
        """
        logging.Logger.__init__(self, logger_name)
        self.logfile = logfile
        self.event_queue = event_queue
        self.level = level

        # Set log level
        self.setLevel(self.level)

        # create formatter
        formatter = logging.Formatter("[%(asctime)s %(levelname)s] [%(name)s.%(module)s.%(funcName)s] %(message)s",)

        # create consoleHandler (default)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(formatter)
        self.addHandler(console_handler)

        # create queue handler for the user interface
        if self.event_queue is not None:
            queue_handler = logging.handlers.QueueHandler(self.event_queue)
            queue_handler.setLevel(self.level)
            queue_handler.setFormatter(formatter)
            self.addHandler(queue_handler)

        # create a file handler to save log
        if self.logfile is not None:
            file_handler = logging.FileHandler(self.logfile, mode='w')
            file_handler.setLevel(self.level)
            file_handler.setFormatter(formatter)
            self.addHandler(file_handler)


if __name__ == '__main__':
    # Logging to a file
    # logging.basicConfig(filename='/Users/peter/Workspace/FincLab/src/example.log', level=logging.DEBUG)
    # logging.debug('This message should go to the log file.')
    # logging.info('So should this one')
    # logging.warning('And this too!')

    # Initialise the event_queue logger
    event_queue = queue.Queue()
    logger = Logger(logger_name='FincLab',
                    logfile="log.txt",
                    event_queue=event_queue,
                    level=logging.DEBUG)

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
    logger.debug('new: debug message')
    logger.info('new: dinfo msg')
    logger.warn('new: dwarn msg')
    logger.error('new: derror msg')
    logger.critical('new: critical msg')
    listener.stop()

    # Testing the log file handler
    print("Testing the log file handler")
    logger.debug('Old: debug message')
    logger.info('Old: info msg')
    logger.warn('Old: warn msg')
    logger.error('Old: error msg')
    logger.critical('Old: critical msg')


    print("Tests complete.")
