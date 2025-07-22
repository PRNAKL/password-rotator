"""Provides a Logger class for structured logging with customizable levels."""

import logging


class Logger:
    """Encapsulates a configurable logger using Python's built-in logging module."""

    def __init__(self):
        """
        Initializes the logger with predefined formatting and INFO level by default.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(__name__)

    def log_message(self, level: int = logging.INFO, message: str = "") -> None:
        """
        Logs a message at the specified log level.

        Args:
            level (int): Logging level (e.g., logging.INFO, logging.ERROR).
            message (str): The message to log.
        """
        self.logger.log(msg=message, level=level)

    @staticmethod
    def pass_method():
        """
        Placeholder method that returns None.

        Returns:
            None
        """
        return None


if __name__ == "__main__":
    LOGGER = Logger()
    LOGGER.log_message(logging.DEBUG, "This is a DEBUG message.")
    LOGGER.log_message(logging.INFO, "This is an INFO message.")
    LOGGER.log_message(logging.WARNING, "This is a WARNING message.")
    LOGGER.log_message(logging.ERROR, "This is an ERROR message.")
    LOGGER.log_message(logging.CRITICAL, "This is a CRITICAL message.")
