import logging
import logging.config

logging.config.fileConfig('config.ini')

# create logger
logger = logging.getLogger('simpleExample')

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

if __name__ == '__main__':
    logger.debug("This is a debug message.")
    logger.info('And an info message --> you so')
    logger.warning('Watch out')
    logger.error("Error message")
    logger.critical("my god, critical error")

