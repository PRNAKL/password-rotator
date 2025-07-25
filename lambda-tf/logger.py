"""Custom Logger utility module for consistent logging across the project."""

import logging


class Logger:
    """A wrapper for Python's logging module with configurable logging levels."""

    def __init__(self):
        """Initialize and configure the logger."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(__name__)

    def log_message(self, level: int = 20, message: str = "") -> None:
        """
        Log a message at the given log level.

        Args:
            level (int): Logging level (e.g., 10=DEBUG, 20=INFO, etc.).
            message (str): Message to be logged.
        """
        self.logger.log(msg=message, level=level)

    @staticmethod
    def pass_method():
        """Placeholder method with no behavior."""
        return None


if __name__ == "__main__":
    logger = Logger()
    # DEBUG: 10
    # INFO: 20
    # WARNING: 30
    # ERROR: 40
    # CRITICAL: 50
    logger.log_message(10, "message")
    logger.log_message(20, "message")
    logger.log_message(30, "message")
    logger.log_message(40, "message")
    logger.log_message(50, "message")
