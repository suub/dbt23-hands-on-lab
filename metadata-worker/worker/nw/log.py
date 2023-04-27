import logging
import sys


__author__ = "Marie-Saphira Flug"
__copyright__ = "Copyright 2022, SuUB"
__license__ = "GPL"
__maintainer__ = "Marie-Saphira Flug"


FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)

    logger.addHandler(get_console_handler())

    # with this pattern, it's rarely necessary to propagate 
    # the error up to parent
    logger.propagate = False

    return logger
