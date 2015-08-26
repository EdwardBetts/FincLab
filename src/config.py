"""
    Module: Load/save configuration to a file.
    Author: Peter Lee

    Usage:
        # Load all config settings from settings.conf
        import lib.config

    Note:
        Use this module to load configuration settings from a file.

    Updates:
        25 Aug 2015: First version

    Sources:
        configparser Quickstart
        https://docs.python.org/3.4/library/configparser.html
"""

import configparser


class Config(object):
    """All settings for the project

    Config files:
        /conf/accounts.conf - User/session token
        /conf/general.conf  - General settings
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

if __name__ == "__main__":
    config = Config('/Users/peter/Workspace/FincLab/settings/')
    print(config.file_general)
    print(config.file_accounts)
    config.set_default()
    config.load()
    for acc in config.accounts.sections():
        print(acc)
        print(config.accounts[acc])
        for item in config.accounts[acc]:
            print(config.accounts[acc][item])
    print('testing')

