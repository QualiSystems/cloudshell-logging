"""Tests for cloudshell.logging.qs_config_parser."""

import os
from unittest import TestCase

from cloudshell.logging.qs_config_parser import QSConfigParser

CUR_DIR = os.path.dirname(__file__)


class TestQSConfigParser(TestCase):
    exp_response = {
        "Logging": {
            "TIME_FORMAT": "%d-%b-%Y--%H-%M-%S",
            "WINDOWS_LOG_PATH": r"{ALLUSERSPROFILE}\QualiSystems\logs",
            "UNIX_LOG_PATH": "/var/log/qualisystems",
            "DEFAULT_LOG_PATH": "../../Logs",
            "LOG_FORMAT": "%(asctime)s [%(levelname)s]: %(name)s "
            "%(module)s - %(funcName)-20s %(message)s",
            "LOG_LEVEL": "ERROR",
            "LOG_PRIORITY": "ENV",
        }
    }

    def setUp(self):
        """Recreate parser before each suite and manage environment variable."""
        # backup existing environment variable
        self.qs_conf = os.getenv("QS_CONFIG")

        os.environ["QS_CONFIG"] = os.path.join(CUR_DIR, "test_qs_config.ini")

    def tearDown(self):
        """Restore environment variable."""
        if self.qs_conf:
            os.environ["QS_CONFIG"] = self.qs_conf
        else:
            del os.environ["QS_CONFIG"]

    def test__get_config_success(self):
        """Test suite for _get_full_config method."""
        self.assertEqual(QSConfigParser()._get_full_config(), self.exp_response)

    def test__get_config_wrong_config_file(self):
        """Test suite for _get_full_config method."""
        os.environ["QS_CONFIG"] = os.path.join(
            CUR_DIR, "config/wrong_conf_file_path.ini"
        )
        self.assertEqual(QSConfigParser()._get_full_config(), {})

    def test_get_config_success(self):
        """Test suite for get_config method."""
        self.assertEqual(QSConfigParser().get_config(), self.exp_response)
        self.assertEqual(
            QSConfigParser().get_config("Logging"), self.exp_response["Logging"]
        )
        self.assertEqual(QSConfigParser().get_config("wrong_section_name"), {})

    def test_get_config_wrong_config_file(self):
        os.environ["QS_CONFIG"] = os.path.join(
            CUR_DIR, "config/wrong_conf_file_path.ini"
        )
        self.assertEqual(QSConfigParser().get_config(), {})
        self.assertEqual(QSConfigParser().get_config("Logging"), {})
