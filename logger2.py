"""
    Class : Logger
        Logs events in the program using five default levels:

    Author: Peter Lee
    Date created: 26 Jan 2016

    Usage
    -----
        >>> from logger import Logger
        >>> import logging, logging.config
        >>> logging.setLoggerClass(Logger)
        >>> logger = logging.getLogger(__name__)  # the logger tracks the package/module hierarchy, and events are logged just from the logger name.
        >>> logger.propagate = False

        >>> logger.debug('debug message')
        >>> logger.info('info msg')
        >>> logger.warn('warn msg')
        >>> logger.error('error msg')
        >>> logger.critical('critical msg')

    Notes
    -----
    Logs can be created in terms of five levels:
        - Debug: Non-critical information
        - Info: Useful information (i.e. some tasks have been completed)
        - Warning: Some non-critical errors
        - Error: Serious bug
        - Critical: Serious bug
"""


import logging
import logging.config


class Logger(logging.Logger):
    """
    The basic logging class.

    Learning resource
    -----------------
    https://docs.python.org/3/howto/logging.html#logging-basic-tutorial

    Logging library
    ---------------
    - Logger: exposes the interface that application code directly uses.
    - Handler: send the log records (creted by loggers) to the appropriate destination.
    - Filter: provide a finer grained facility for determining which log records to output.
    - Formatter: specify the layout of log records in the final output.
    """

    def __init__(self, name, level=logging.DEBUG):
        """
        Initialises the Logger class.

        Parameters
        ----------
        name : string
            The name of the module

        level : logging.XXXXX (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            The minimum level of message to be reproted.
        """
        logging.Logger.__init__(self, name)
        self.name = name
        self.level = level

        self.setLevel(self.level)

        # create formatter
        formatter = logging.Formatter("[%(asctime)s %(levelname)s] [%(name)s.%(module)s.%(funcName)s] %(message)s",
                                      )
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(self.level)
        ch.setFormatter(formatter)

        # add ch to logger
        self.addHandler(ch)


logging.setLoggerClass(Logger)
logger = logging.getLogger(__name__)
logger.propagate = False


if __name__ == '__main__':
    """
    Learning source:
        https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    """
    # Logging to a file
    # logging.basicConfig(filename='/Users/peter/Workspace/FincLab/src/example.log', level=logging.DEBUG)
    # logging.debug('This message should go to the log file.')
    # logging.info('So should this one')
    # logging.warning('And this too!')

    logging.setLoggerClass(Logger)
    logger = logging.getLogger(__name__)
    logger.propagate = False

    logger.debug('debug message')
    logger.info('info msg')
    logger.warn('warn msg')
    logger.error('error msg')
    logger.critical('critical msg')

    logging.setLoggerClass(SimpleLogger)
    logger2 = logging.getLogger(__name__)
    logger2.propagate = False

    logger2.debug('debug message')
    logger2.info('info msg')
    logger2.warn('warn msg')
    logger2.error('error msg')
    logger2.critical('critical msg')

    print("Tests complete.")
