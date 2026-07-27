import logging

from config import DEBUG_LOG


def get_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    logger.setLevel(logging.DEBUG if DEBUG_LOG == 1 else logging.CRITICAL + 1)
    return logger
