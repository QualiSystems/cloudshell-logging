import configparser as ConfigParser
import os

DEFAULT_CONFIG_PATH = "qs_config.ini"


class QSConfigParser:
    _configDict = None

    def __init__(self):
        self._config_parser = ConfigParser.RawConfigParser()

    def _get_full_config(self):
        config_file = os.getenv(
            "QS_CONFIG", os.path.join(os.path.dirname(__file__), DEFAULT_CONFIG_PATH)
        )
        config_dict = {}
        try:
            self._config_parser.read(config_file)

            for section in self._config_parser.sections():
                config_dict[section] = {}
                for key, val in self._config_parser.items(section):
                    config_dict[section][key.upper()] = val.strip("'")
        except Exception:
            pass

        return config_dict

    def get_config(self, section=None):
        if section is not None:
            return self._get_full_config().get(section, {})
        else:
            return self._get_full_config()
