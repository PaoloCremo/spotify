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

    '''
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    PRINT_LEVEL = logging.WARNING
    LOGGER_LEVEL = logging.INFO
    print_formatter = logging.Formatter(
        "%(asctime)s spytify %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    ch.setFormatter(print_formatter)
    ch.setLevel(PRINT_LEVEL)

    logfile = "spytify.log"
    fh = logging.FileHandler(logfile)
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s][%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(formatter)
    fh.setLevel(LOGGER_LEVEL)

    logger.addHandler(ch)
    logger.addHandler(fh)
    '''

    return logger
