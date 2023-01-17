import logging

def get_logger() -> logging.Logger:
    logging.basicConfig(
        format="[%(levelname)s %(asctime)s]: %(message)s", 
        level=logging.INFO, datefmt='%d-%m-%y %H:%M:%S'
    )

    logger = logging.getLogger()
    return logger

LOG = get_logger()
