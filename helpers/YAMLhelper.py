import yaml
from pathlib import Path

myself = Path(__file__).resolve()


class YAMLhelper(object):  # Singleton pattern
    __settings__ = None
    __settings_file__ = str(myself.parents[1] / 'settings/settings.yaml')

    def __new__(cls, settings_file=None):
        if not hasattr(cls, 'instance'):
            cls.instance = super(YAMLhelper, cls).__new__(cls)
        return cls.instance

    def __init__(self, settings_file=None):
        if not settings_file:
            settings_file = self.__settings_file__
        if not self.__settings__:
            with open(settings_file, "r") as stream:
                self.__settings__ = yaml.safe_load(stream)

    def get_networks(self) -> list:
        """

        :return: list of networks for scan from section networks of settings/settings.yaml
        """
        if self.__settings__:
            return self.__settings__['networks']


    def get_user(self) -> dict:
        """

        :return: dict {'usr': username, 'pwd': userpassword} from section user of settings/settings.yaml
        """
        if self.__settings__:
            if not 'user' in self.__settings__:
                return False
            return self.__settings__['user']


    def get_db_connection(self) -> str:
        """

        :return: a string to connect to the database in the format postgresql://dbuser:userpwd@localhost:5432/dbname
        """
        if self.__settings__:
            return self.__settings__['db_connection']['dbms'] + \
                   '://' + \
                   self.__settings__['db_connection']['usr'] + \
                   ':' + \
                   self.__settings__['db_connection']['pwd'] + \
                   '@' + \
                   self.__settings__['db_connection']['host'] + \
                   ':' + \
                   str(self.__settings__['db_connection']['port']) + \
                   '/' + \
                   self.__settings__['db_connection']['db']
