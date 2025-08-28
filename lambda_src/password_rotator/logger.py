"""Custom logger wrapper around Python's logging module."""

import logging


class Logger:
    """A wrapper for Python's logging module with configurable logging levels."""

    def __init__(self) -> None:
        """Initialize and configure the logger."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(__name__)

    def log_message(self, level: int = logging.INFO, message: str = "") -> None:
        """
        Log a message at the given log level.

        Args:
            level (int): Logging level (e.g., 10=DEBUG, 20=INFO, etc.).
            message (str): Message to be logged.
        """
        self.logger.log(level=level, msg=message)

    def debug(self, message: str) -> None:
        """
        Log a message with DEBUG level.

        Args:
            message (str): The debug message to be logged.

        Returns:
            None
        """
        self.log_message(logging.DEBUG, message)

    def info(self, message: str) -> None:
        """
        Log a message with INFO level.

        Args:
            message (str): The informational message to be logged.

        Returns:
            None
        """
        self.log_message(logging.INFO, message)

    def warning(self, message: str) -> None:
        """
        Log a message with WARNING level.

        Args:
            message (str): The warning message to be logged.

        Returns:
            None
        """
        self.log_message(logging.WARNING, message)

    def error(self, message: str) -> None:
        """
        Log a message with ERROR level.

        Args:
            message (str): The error message to be logged.

        Returns:
            None
        """
        self.log_message(logging.ERROR, message)

    def critical(self, message: str) -> None:
        """
        Log a message with CRITICAL level.

        Args:
            message (str): The critical message to be logged.

        Returns:
            None
        """
        self.log_message(logging.CRITICAL, message)


if __name__ == "__main__":
    LOGGER = Logger()
    LOGGER.debug("This is a debug message")
    LOGGER.info("This is an info message")
    LOGGER.warning("This is a warning message")
    LOGGER.error("This is an error message")
    LOGGER.critical("This is a critical message")
