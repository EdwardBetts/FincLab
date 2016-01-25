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

import configparser
import os.path


class Configuration(configparser.ConfigParser):
    """
    Class - the configuration settings.
    """

    def __init__(self, config_folder='', config_file='config.ini'):
        """
        Initialises the configparser object.

        Parameters
        ----------
            config_file : string, default 'config.ini'
                Full path to the config file or simply the filename if located in the home folder of the app.
        """
        configparser.ConfigParser.__init__(self)
        self.config_file = os.path.join(config_folder, config_file)

        self.load()  # Load settings

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
    config = Configuration()
    config.reset_to_defaults()
    print(config.sections())
    print(config["notes"]["Author"])
    config.save()

