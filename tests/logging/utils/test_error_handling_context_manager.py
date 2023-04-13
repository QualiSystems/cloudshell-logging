from unittest import TestCase
from unittest.mock import MagicMock, Mock

from cloudshell.logging.utils.error_handling_context_manager import (
    ErrorHandlingContextManager,
)


class TestErrorHandlingContextManager(TestCase):
    def test_log_written_when_exception_occurs(self):
        # Arrange
        logger = Mock()
        logger.error = MagicMock()
        try:

            # Act
            with ErrorHandlingContextManager(logger=logger):
                raise ValueError("some value error occurred")
        except ValueError:

            # Assert
            logger.error.assert_called()

    def test_log_not_written_when_exception_not_thrown(self):
        # Arrange
        logger = Mock()
        logger.error = MagicMock()

        # Act
        with ErrorHandlingContextManager(logger=logger):
            print("hello world")  # noqa: T201

        # Assert
        logger.error.assert_not_called()
