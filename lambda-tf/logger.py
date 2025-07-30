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

    def debug(self, message: str) -> None:
        """Log a message with DEBUG level."""
        self.log_message(logging.DEBUG, message)

    def info(self, message: str) -> None:
        """Log a message with INFO level."""
        self.log_message(logging.INFO, message)

    def warning(self, message: str) -> None:
        """Log a message with WARNING level."""
        self.log_message(logging.WARNING, message)

    def error(self, message: str) -> None:
        """Log a message with ERROR level."""
        self.log_message(logging.ERROR, message)

    def critical(self, message: str) -> None:
        """Log a message with CRITICAL level."""
        self.log_message(logging.CRITICAL, message)

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
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
