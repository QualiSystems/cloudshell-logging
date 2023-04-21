"""Tests for cloudshell.logging.qs_logger."""

import logging
import os
import shutil
from logging import FileHandler
from unittest import TestCase, mock
from unittest.mock import MagicMock

from cloudshell.logging import qs_logger
from cloudshell.logging.memory_handler import LimitedMemoryHandler

CUR_DIR = os.path.dirname(__file__)
full_settings = MagicMock(
    return_value={
        "LOG_PATH": "../../Logs",
        "TIME_FORMAT": "%d-%b-%Y--%H-%M-%S",
        "LOG_LEVEL": "ERROR",
        "LOG_PRIORITY": "ENV",
        "LOG_FORMAT": "%(asctime)s [%(levelname)s]: %(name)s %(module)s - "
        "%(funcName)-20s %(message)s",
        "MEMORY_LOG_SIZE": 500,
    }
)

cut_settings = MagicMock(
    return_value={
        "TIME_FORMAT": "%d-%b-%Y--%H-%M-%S",
        "LOG_LEVEL": "ERROR",
        "LOG_PRIORITY": "ENV",
        "LOG_FORMAT": "%(asctime)s [%(levelname)s]: %(name)s %(module)s - "
        "%(funcName)-20s %(message)s",
    }
)

wrong_settings = MagicMock(
    return_value={
        "LOG_PATH": None,
        "TIME_FORMAT": "%d-%b-%Y--%H-%M-%S",
        "LOG_LEVEL": "ERROR",
        "LOG_FORMAT": "%(asctime)s [%(levelname)s]: %(name)s %(module)s - "
        "%(funcName)-20s %(message)s",
    }
)


class TestQSLogger(TestCase):
    _LOGS_PATH = os.path.join(os.path.dirname(__file__), "../../Logs")

    def setUp(self):
        """Remove all existing test Logs folders before each suite."""
        self.get_settings = qs_logger.get_settings
        self.qs_conf = os.getenv("QS_CONFIG")
        self.log_path = os.getenv("LOG_PATH")

        os.environ["QS_CONFIG"] = os.path.join(CUR_DIR, "test_qs_config.ini")
        os.environ["LOG_PATH"] = os.path.join(CUR_DIR, "../../Logs")

        if os.path.exists(self._LOGS_PATH):
            shutil.rmtree(self._LOGS_PATH)

    def tearDown(self):
        """Close all existing logging handlers after each suite."""
        if self.qs_conf:
            os.environ["QS_CONFIG"] = self.qs_conf
        elif "QS_CONFIG" in os.environ:
            del os.environ["QS_CONFIG"]

        if self.log_path:
            os.putenv("LOG_PATH", self.log_path)
        elif "LOG_PATH" in os.environ:
            del os.environ["LOG_PATH"]
        if "LOG_LEVEL" in os.environ:
            del os.environ["LOG_LEVEL"]

        for logger in qs_logger._LOGGER_CONTAINER.values():
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()

        qs_logger._LOGGER_CONTAINER.clear()

        qs_logger.get_settings = self.get_settings

    @mock.patch.dict("cloudshell.logging.qs_logger.os.environ", {"LOG_LEVEL": "DEBUG"})
    def test_get_settings_priority_env_default_level(self):
        """Test suite for get_settings method.

        Priority set to ENV but LOG_LEVEL variable does't exist
        """
        exp_response = {
            "WINDOWS_LOG_PATH": r"{ALLUSERSPROFILE}\QualiSystems\logs",
            "UNIX_LOG_PATH": "/var/log/qualisystems",
            "DEFAULT_LOG_PATH": "../../Logs",
            "TIME_FORMAT": "%d-%b-%Y--%H-%M-%S",
            "LOG_LEVEL": qs_logger.DEFAULT_LEVEL,
            "LOG_PRIORITY": "ENV",
            "LOG_FORMAT": "%(asctime)s [%(levelname)s]: %(name)s %(module)s - "
            "%(funcName)-20s %(message)s",
            "MEMORY_LOG_SIZE": 500,
        }
        names_to_remove = ["LOG_LEVEL"]
        modified_environ = {
            k: v for k, v in os.environ.items() if k not in names_to_remove
        }
        with mock.patch.dict(os.environ, modified_environ, clear=True):
            self.assertEqual(qs_logger.get_settings(), exp_response)

    def test_get_settings_priority_env(self):
        """Test suite for get_settings method.

        Priority set to ENV and LOG_LEVEL variable exists
        """
        exp_response = {
            "WINDOWS_LOG_PATH": r"{ALLUSERSPROFILE}\QualiSystems\logs",
            "UNIX_LOG_PATH": "/var/log/qualisystems",
            "DEFAULT_LOG_PATH": "../../Logs",
            "TIME_FORMAT": "%d-%b-%Y--%H-%M-%S",
            "LOG_LEVEL": "DEBUG",
            "LOG_PRIORITY": "ENV",
            "LOG_FORMAT": "%(asctime)s [%(levelname)s]: %(name)s %(module)s - "
            "%(funcName)-20s %(message)s",
            "MEMORY_LOG_SIZE": 500,
        }
        with mock.patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            self.assertEqual(qs_logger.get_settings(), exp_response)

    @mock.patch("cloudshell.logging.qs_logger.QSConfigParser")
    def test_get_settings_default_log_level(self, parser_class):
        """Test suite for get_settings method.

        Wrong priority variable -> DEFAULT LOG LEVEL
        """
        parser = parser_class.return_value
        parser.get_config.return_value = {"LOG_PRIORITY": "WRONG_PRIORITY"}

        exp_response = {
            "TIME_FORMAT": qs_logger.DEFAULT_TIME_FORMAT,
            "LOG_LEVEL": qs_logger.DEFAULT_LEVEL,
            "LOG_PRIORITY": "WRONG_PRIORITY",
            "LOG_FORMAT": qs_logger.DEFAULT_FORMAT,
            "MEMORY_LOG_SIZE": 500,
        }

        self.assertEqual(qs_logger.get_settings(), exp_response)

    @mock.patch("cloudshell.logging.qs_logger.QSConfigParser")
    def test_get_settings_log_level_from_config(self, parser_class):
        """Test suite for get_settings method.

        Get LOG_LEVEL from configuration file
        """
        parser = parser_class.return_value
        parser.get_config.return_value = {
            "LOG_PRIORITY": "CONFIG",
            "LOG_LEVEL": "CRITICAL",
        }

        exp_response = {
            "TIME_FORMAT": qs_logger.DEFAULT_TIME_FORMAT,
            "LOG_LEVEL": "CRITICAL",
            "LOG_PRIORITY": "CONFIG",
            "LOG_FORMAT": qs_logger.DEFAULT_FORMAT,
            "MEMORY_LOG_SIZE": 500,
        }

        self.assertEqual(qs_logger.get_settings(), exp_response)

    @mock.patch("cloudshell.logging.qs_logger.os")
    def test_get_log_path_config_from_environment_variable(self, os):
        """Check that method will primarily return log path.

        The log path should be from the environment variable if such exists
        """
        config = {}
        expected_path = MagicMock()
        os.environ = {"LOG_PATH": expected_path}
        # act
        result = qs_logger._get_log_path_config(config=config)
        # verify
        self.assertEqual(result, expected_path)

    @mock.patch("cloudshell.logging.qs_logger.os")
    def test_get_log_path_config_for_windows_os(self, os):
        """Check that method will return windows log path setting.

        Setting should be with substituted environment variables
        """
        os.name = qs_logger.WINDOWS_OS_FAMILY
        os.environ = {"SOME_EN_VARIABLE": "C:\\some_path"}
        expected_path = "{SOME_EN_VARIABLE}\\qualisystems\\logs\\commands"
        config = {"WINDOWS_LOG_PATH": expected_path}
        # act
        result = qs_logger._get_log_path_config(config=config)
        # verify
        self.assertEqual(result, "C:\\some_path\\qualisystems\\logs\\commands")

    @mock.patch("cloudshell.logging.qs_logger.os")
    def test_get_log_path_config_for_unix_os(self, os):
        """Check that method will return unix log path setting for posix OS."""
        os.name = "posix"
        expected_path = MagicMock()
        config = {"UNIX_LOG_PATH": expected_path}
        # act
        result = qs_logger._get_log_path_config(config=config)
        # verify
        self.assertEqual(result, expected_path)

    def test_get_accessible_log_path_default_params(self):
        """Test suite for get_accessible_log_path method."""
        path = qs_logger.get_accessible_log_path()
        self.assertRegex(
            path,
            r"Logs[\\/]Autoload[\\/](.*[\\/])?default--\d{2}-\w+-"
            r"\d{4}--\d{2}-\d{2}-\d{2}\.log",
        )
        self.assertTrue(os.path.dirname(path))

    def test_get_accessible_log_path_path_creation(self):
        """Test suite for get_accessible_log_path method."""
        path = qs_logger.get_accessible_log_path()
        self.assertTrue(os.path.dirname(path))

    def test_get_accessible_log_path(self):
        """Test suite for get_accessible_log_path method."""
        path = qs_logger.get_accessible_log_path("reservation_id", "handler_name")
        self.assertRegex(
            path,
            r"Logs[\\/]reservation_id[\\/](.*[\\/])?"
            r"handler_name--\d{2}-\w+-\d{4}--\d{2}-\d{2}-\d{2}\.log",
        )

    def test_get_accessible_log_path_log_path_setting_missing(self):
        """Test suite for get_accessible_log_path method."""
        if "LOG_PATH" in os.environ:
            del os.environ["LOG_PATH"]
        qs_logger.get_settings = cut_settings
        self.assertIsNone(qs_logger.get_accessible_log_path())

    def test_get_accessible_log_path_log_path_is_none(self):
        """Test suite for get_accessible_log_path method."""
        if "LOG_PATH" in os.environ:
            del os.environ["LOG_PATH"]
        qs_logger.get_settings = wrong_settings
        self.assertIsNone(qs_logger.get_accessible_log_path())

    def test_get_qs_logger_full_settings_default_params(self):
        """Test suite for get_qs_logger method."""
        qs_logger.get_settings = full_settings
        assert isinstance(qs_logger.get_qs_logger().handlers[0], FileHandler)

    def test_get_qs_logger_full_settings(self):
        """Test suite for get_qs_logger method."""
        qs_logger.get_settings = full_settings
        assert isinstance(qs_logger.get_qs_logger("test1").handlers[0], FileHandler)

    def test_get_qs_logger_stream_handler(self):
        """Test suite for get_qs_logger method."""
        if "LOG_PATH" in os.environ:
            del os.environ["LOG_PATH"]
        qs_logger.get_settings = cut_settings

        logger = qs_logger.get_qs_logger(log_group="stream")
        # the logger has several handlers cause of previous tests
        # but log records would be filtered by context
        assert isinstance(logger.handlers[-1], logging.StreamHandler)

    def test_get_qs_logger_container_filling(self):
        """Test suite for get_qs_logger method."""
        qs_logger.get_settings = full_settings
        qs_logger.get_qs_logger()
        qs_logger.get_qs_logger(log_group="test1")

        if "LOG_PATH" in os.environ:
            del os.environ["LOG_PATH"]
        qs_logger.get_settings = cut_settings
        qs_logger.get_qs_logger(log_group="test2")

        self.assertEqual(
            sorted(qs_logger._LOGGER_CONTAINER.keys()),
            sorted(["Ungrouped", "test1", "test2"]),
        )

    def test_get_qs_logger_log_level_incorrect(self):
        os.environ["LOG_LEVEL"] = "INCORRECT"
        logger = qs_logger.get_qs_logger()
        assert logger.level == logging.DEBUG
        for hdrl in logger.handlers:
            if isinstance(hdrl, LimitedMemoryHandler):
                assert hdrl.level == logging.NOTSET
            else:
                assert hdrl.level == getattr(logging, qs_logger.DEFAULT_LEVEL)

    def test_normalize_buffer_decolorize(self):
        """Test suite for normalize_buffer method."""
        self.assertEqual(
            qs_logger.normalize_buffer(
                "\033[1;32;40mGreenOnWhiteBack "
                "\033[4;31mRedUnderscore "
                "\033[93mYellow"
            ),
            "GreenOnWhiteBack RedUnderscore Yellow",
        )

    def test_normalize_buffer_remove_hex_symbols(self):
        """Test suite for normalize_buffer method."""
        self.assertEqual(
            qs_logger.normalize_buffer("\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff"), "---"
        )

    def test_normalize_buffer_carriage_return_replacing(self):
        """Test suite for normalize_buffer method."""
        self.assertEqual(qs_logger.normalize_buffer("\r\n \n\r"), "\n \n\r")

    def test_normalize_buffer_converts_tuple_to_string(self):
        """Test suite for normalize_buffer method."""
        self.assertEqual(
            qs_logger.normalize_buffer(("test", "tuple")), "('test', 'tuple')"
        )

    def test_normalize_buffer_converts_dict_to_string(self):
        """Test suite for normalize_buffer method."""
        self.assertEqual(
            qs_logger.normalize_buffer({"test": "dict"}), "{'test': 'dict'}"
        )
