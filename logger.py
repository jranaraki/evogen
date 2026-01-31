""" This is the EVOGEN logger
"""

import logging
import sys


def get_logger():
    """
    Returns a logger object
    :return: Logger object
    """

    logger = logging.getLogger('evogen')
    logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger