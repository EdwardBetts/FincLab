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
        #formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(self.level)
        ch.setFormatter(formatter)

        # add ch to logger
        self.addHandler(ch)


if __name__=='__main__':
    """
    Learning source:
        https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    """
    # A simple example
    logging.warning('Watch out!') # will print a message to the console
    logging.info("Nothing will be printed.") # will not print anything

    # Logging to a file
    #logging.basicConfig(filename='example.log', level=logging.DEBUG)
    #logging.debug('This message should go to the log file.')
    #logging.info('So should this one')
    #logging.warning('And this too!')

    logging.setLoggerClass(FincLogger)
    logger = logging.getLogger(__name__) # the logger tracks the package/module hierarchy, and events are logged just from the logger name.
    logger.propagate = False

    logger.debug('debug message')
    logger.info('info msg')
    logger.warn('warn msg')
    logger.error('error msg')
    logger.critical('critical msg')

    print('WTFWTF!')
    print('yoyo')
