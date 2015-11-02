"""
    Module: Load/save configuration to a file.
    Author: Peter Lee (Sep 2015)

    Usage:
        # Load all config settings
        >>> import lib.config

        # To reset configuration files
        >>> Reset_Settings.set_default()
        >>> Load new configurations
        Config = Configuration(folder + 'general.conf',
                           folder + 'accounts.conf')

    Note:
        Use this module to load configuration settings from a file.

    Sources:
        configparser Quickstart
        https://docs.python.org/3.4/library/configparser.html
"""

import configparser
import os


class Configuration:
    """
    Base class that takes a number of .conf files and update items in the form
    of dicts.

    Config files:
        /conf/accounts.conf - User/session token
        /conf/general.conf  - General settings

    Usage:
    config = Configuration('/Users/peter/Workspace/FincLab/settings/')

    config.restore_to_defaults()
        Generate default setting files for the project

    config.save()
        Save the current settings to file
    """
    def __init__(self, conf_folder):
        # Define config file names
        self.conf_folder = conf_folder
        self.file_general = conf_folder + 'general.conf'
        self.file_accounts = conf_folder + 'accounts.conf'
        self.conf_files = (self.file_general,
                           self.file_accounts)

        # Load settings from files
        self.load()

    def load(self):
        """
        Load settings from a file.
        """
        # Alternative method (Disabled)
        # Because it cannot differentiate between accounts
        # Initiate the parser
        # parser = configparser.SafeConfigParser()
        # parser.optionxform = str  # make option names case sensitive
        # found = parser.read(self.conf_files)

        # if not found:
        #    raise ValueError("Config file " + self.conf_files + " is not found!")
        # else:
        #     for section in parser.sections():
        #         self.__dict__.update(parser.items(section))

        # Load config files
        self.general = configparser.ConfigParser()
        self.general.read(self.file_general)
        self.accounts = configparser.ConfigParser()
        self.accounts.read(self.file_accounts)

    def restore_to_defaults(self):
        """
        Restore all settings to default values
        """
        # general.conf
        self.general = configparser.ConfigParser()
        self.general['DEFAULT'] = {
            'AppName': 'FincLab',
            'Author': 'Peter Lee',
            'Author Email': 'mr.peter.lee@hotmail.com'
        }

        # accounts.conf
        self.accounts = configparser.ConfigParser()
        self.accounts['Acc1'] = {
            "consumer_key": "dj0yJmk9VWo0RXhCSk80MmlQJmQ9WVdrOVNXRjFOa2cwTm1zbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD1hYw--",
            "consumer_secret": "0d0c9222ce8533a5e1350e38f9216ef633561289"
        }

        self.save()
        self.load()

    def save(self):
        """
        Save settings to a file.
        """
        with open(self.file_general, 'w') as configfile:
            self.general.write(configfile)
        with open(self.file_accounts, 'w') as configfile:
            self.accounts.write(configfile)

    def save_accounts(self):
        """
        Save only account.conf
        """
        with open(self.file_accounts, 'w') as configfile:
            self.accounts.write(configfile)


class Gen_Default_Config:
    """Generate default setting files for the project

    Config files:
        /conf/accounts.conf - User/session token
        /conf/general.conf  - General settings

    Usage:
        reset = Gen_Default_Config('/Users/peter/Workspace/FincLab/settings/')
    """
    def __init__(self, conf_folder):
        # Define config file names
        self.conf_folder = conf_folder
        self.file_general = conf_folder + 'general.conf'
        self.file_accounts = conf_folder + 'accounts.conf'

        self.load()

    def set_default(self):
        """
        Restore all settings to default values
        """
        # general.conf
        self.general = configparser.ConfigParser()
        self.general['DEFAULT'] = {
            'AppName': 'FincLab',
            'Author': 'Peter Lee',
            'Author Email': 'mr.peter.lee@hotmail.com'
        }

        # accounts.conf
        self.accounts = configparser.ConfigParser()
        self.accounts['Acc1'] = {
            "consumer_key": "dj0yJmk9VWo0RXhCSk80MmlQJmQ9WVdrOVNXRjFOa2cwTm1zbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD1hYw--",
            "consumer_secret": "0d0c9222ce8533a5e1350e38f9216ef633561289"
        }

        self.save()

    def save(self):
        """
        Save settings to a file.
        """
        with open(self.file_general, 'w') as configfile:
            self.general.write(configfile)
        with open(self.file_accounts, 'w') as configfile:
            self.accounts.write(configfile)

    def save_accounts(self):
        """
        Save accounts settings only.
        """
        with open(self.file_accounts, 'w') as configfile:
            self.accounts.write(configfile)

    def load(self):
        """
        Load settings from a file.
        """
        # Load config files
        self.general = configparser.ConfigParser()
        self.general.read(self.file_general)
        self.accounts = configparser.ConfigParser()
        self.accounts.read(self.file_accounts)


folder = '/Users/peter/Workspace/FincLab/settings/'
# Check if the default settings folder exist
Config = Configuration(folder)

if __name__ == "__main__":
    print('Reset settings to default values')
    Config.restore_to_defaults()

    print('Inspect each account')
    for index, acc in enumerate(Config.accounts.sections()):
        print('Account', index, ':', acc)
        print(Config.accounts[acc])
        for item in Config.accounts[acc]:
            print("file accounts.conf")
            print("Section:", acc)
            print("Item:", item)
            print("Value:", Config.accounts[acc][item])

    print("Tests complete!")
