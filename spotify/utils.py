import logging

def setup_logger() -> "logging.Logger":
    """Setup a logger for the module"""

    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    ch = logging.StreamHandler()
    print_formatter = logging.Formatter(
        "%(asctime)s spytify %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    ch.setFormatter(print_formatter)
    logger.addHandler(ch)

    return logger
