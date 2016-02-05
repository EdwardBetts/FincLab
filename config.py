import configparser
import os.path
import datetime as dt
import pandas as pd

"""
Class : Config

Author: Peter Lee
Date created: 25 Jan 2016

The module loads and saves to the configuration file (default 'config.ini').

Usage
-----
    Load all config settings
    >>> from config import config

    Reset to default settings
    >>> config.reset_to_defaults()

    Save new settings
    >>> config.save()

    Reload settings
    >>> config.load()

Notes
-----
    Check the documentation: https://docs.python.org/3/library/configparser.html
    and make sure do not overwrite default methods while creating new ones.
"""


class Configuration(configparser.ConfigParser):
    """
    Class - the configuration settings.
    """

    def __init__(self, config_folder='', config_file='config.ini'):
        """
        Initialises the configparser object.

        Parameters
        ----------
            config_folder : string, default ''
                Folder to the config file.
            config_file : string, default 'config.ini'
                Full path to the config file or simply the filename if located in the home folder of the app.
        """
        configparser.ConfigParser.__init__(self)
        self.config_file = os.path.join(config_folder, config_file)

        self.load()  # Load settings

        # Parse dates
        self.remote_timezone = self['general']['remote_timezone']
        self.local_timezone = self['general']['local_timezone']

        start_date = self['data']['start_date'] + ' 00:00:00'
        self.dt_start_date = pd.Timestamp(start_date, tz=self.remote_timezone)

        # Simply get the last business day on or before the current day
        end_date = self['data']['end_date']
        if end_date.upper() == "NONE":
            self.dt_end_date = pd.Timestamp(dt.datetime.now(), tz=self.local_timezone)
            self.dt_end_date = self.dt_end_date.tz_convert(self.remote_timezone)
        else:
            end_date = self['data']['end_date'] + ' 18:00:00'
            self.dt_end_date = pd.Timestamp(end_date, tz=self.remote_timezone)
        self.dt_end_date -= 3 * pd.tseries.offsets.BDay()

    def load(self):
        """
        Load settings from the config file, default 'config.ini'.
        """
        try:
            self.read(self.config_file)
        except IOError as e:
            print("Error:", e)
            raise e

    def save(self):
        """
        Save settings to the config file, default "config.ini"
        """
        with open(self.config_file, 'w') as configfile:
            self.write(configfile)

    def reset_to_defaults(self):
        """
        Reset settings to defaults.
        """
        if not self.has_section("notes"):
            self.add_section("notes")
        self.set("notes", "author", "Peter Lee")
        self.set("notes", "email", "mr.peter.lee@hotmail.com")

        if not self.has_section("components"):
            self.add_section("components")
        self.set("components", "strategy", "MovingAverageCrossover")
        self.set("components", "data_handler", "HistoricDataHandler")
        self.set("components", "execution_handler", "SimulatedExecutionHandler")

config = Configuration()


if __name__ == '__main__':
    print("debugging...")
    # config = Configuration()
    # config.reset_to_defaults()
    print(config.sections())
    print(config["notes"]["Author"])
    # config.save()
    print("UTC", config.remote_timezone)
    print("Start date: ", config.dt_start_date)
    print("End date: ", config.dt_end_date)

