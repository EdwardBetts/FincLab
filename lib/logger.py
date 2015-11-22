"""
    Module: Logs events in the program using five default levels:
    Author: Peter Lee

    Usage:
        >>> from lib.logger import FincLogger
        >>> import logging, logging.config
        >>> logging.setLoggerClass(FincLogger)
        >>> logger = logging.getLogger(__name__)  # the logger tracks the package/module hierarchy, and events are logged just from the logger name.
        >>> logger.propagate = False

        >>> logger.debug('debug message')
        >>> logger.info('info msg')
        >>> logger.warn('warn msg')
        >>> logger.error('error msg')
        >>> logger.critical('critical msg')

    Note: A total of five levels:
        - Debug: Non-critical information
        - Info: Useful information (i.e. some tasks have been completed)
        - Warning: Some non-critical errors
        - Error: Serious bug
        - Critical: Serious bug
    The logger class shall be implemented in the program whenever possible.

    Sources:
        configparser Quickstart
        https://docs.python.org/3.4/library/configparser.html
"""


# Logger
import logging
import logging.config
# from logging import Logger, handlers


class FincLogger(logging.Logger):
    """
    Yahoo! Logger class

    Date: 23 Aug 2015

    Learning resource:
        https://docs.python.org/3/howto/logging.html#logging-basic-tutorial

    Logging library:
        - Logger: exposes the interface that application code directly
        uses.
        - Handler: send the log records (creted by loggers) to the
        appropriate destination.
        - Filter: provide a finer grained facility for determining
        which log records to output.
        - Formatter: specify the layout of log records in the final
        output.
    """

    def __init__(self, name, level=logging.DEBUG):
        """
        - name : logger name
        - filename : file containing logs
        """
        super(FincLogger, self).__init__(name)
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


class SimpleLogger(logging.Logger):
    """
    A simpler logger without headers.
    """

    def __init__(self, name, level=logging.DEBUG):
        """
        - name : logger name
        - filename : file containing logs
        """
        super(SimpleLogger, self).__init__(name)
        self.name = name
        self.level = level

        self.setLevel(self.level)

        # create formatter
        formatter = logging.Formatter("[%(name)s %(asctime)s %(levelname)s]  %(message)s",
                                      )
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(self.level)
        ch.setFormatter(formatter)

        # add ch to logger
        self.addHandler(ch)


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

    logging.setLoggerClass(FincLogger)
    logger = logging.getLogger(__name__)  # the logger tracks the package/module hierarchy, and events are logged just from the logger name.
    logger.propagate = False

    logger.debug('debug message')
    logger.info('info msg')
    logger.warn('warn msg')
    logger.error('error msg')
    logger.critical('critical msg')

    print("Tests complete.")
