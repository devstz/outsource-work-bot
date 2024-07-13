import logging
from datetime import datetime

def setup_logging(time_session: datetime) -> None:
    """
    Sets up logging to four different files with different log levels.

    Args:
        time_session (datetime): The current time session.
    """
    # Create a logger
    logger = logging.getLogger()
    time = time_session.strftime("%Y-%m-%d_%H-%M-%S")

    # Set the logging level to DEBUG to capture all log messages
    logger.setLevel(logging.DEBUG)
    path = 'data/logger/log_history_'

    # Create four file handlers with different log levels
    info_handler = logging.FileHandler(f'{path}info/log_{time}_INFO.txt')
    info_handler.setLevel(logging.INFO)

    critical_handler = logging.FileHandler(f'{path}critical/log_{time}_CRITICAL.txt')
    critical_handler.setLevel(logging.CRITICAL)

    error_handler = logging.FileHandler(f'{path}error/log_{time}_ERROR.txt')
    error_handler.setLevel(logging.ERROR)

    debug_handler = logging.FileHandler(f'{path}debug/log_{time}_DEBUG.txt')
    debug_handler.setLevel(logging.DEBUG)
    
    # Create a console handler with DEBUG level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create a formatter and attach it to each handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    info_handler.setFormatter(formatter)
    critical_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    debug_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(info_handler)
    logger.addHandler(critical_handler)
    logger.addHandler(error_handler)
    logger.addHandler(debug_handler)
    logger.addHandler(console_handler)