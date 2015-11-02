"""
    Module: FincLab

    Author: Peter Lee
"""
import configparser
import logging
import logging.config
import importlib

from lib.config import Config
from lib.yql_auth import YahooOAuth
import lib
importlib.reload(lib.config)
importlib.reload(lib.yql_auth)


def main():
    """ Environmental variables:
        settings_folder     : Default folder settings file
    """
    settings_folder = '/Users/peter/Workspace/FincLab/settings/'

    # Initiate a logger
    logging.config.fileConfig(settings_folder + 'log.conf')
    logger = logging.getLogger('FincLab')

    # Load program settings
    config = lib.config.Configuration(settings_folder)
    for acc in config.accounts.sections():  # Show account info
        for item in config.accounts[acc]:
            logger.info('# ' + acc + ' credentials' +
                        ' - ' + item + ': ' +
                        config.accounts[acc][item])

    # Initiate a session
    logger.debug('Resetting settings conf.')
    config.set_default()
    print(config)
    yf = lib.yql_auth.YahooOAuth(config=config, logger=logger)
    logger.debug('get_nonce()' + yf.get_nonce())
    print(yf.parse('select * from yahoo.finance.historicaldata where symbol = "YHOO" and startDate = "2009-09-11" and endDate = "2010-03-10"'))
    print('Done!')

if __name__ == "__main__":
    main()


