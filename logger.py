import logging

class Logger:
    """ *** DOC STRING *** """
    def __init__(self):
        # Create logger
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(__name__)

    def log_message(self, level: int = 20, message: str = "") -> None:
        """ *** DOC STRING *** """
        # reference logger via self, set the level of the logger if level is present
        # log message at that level.
        self.logger.log(msg=message, level=level)

    @staticmethod
    def pass_method():
        """*** DOC STRING *** """
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