import sys

from loguru import logger

logger.remove()

log_format = "{time:YYYY-MM-DD HH:mm:ss} | <lvl>{level:^8}</lvl> | {message} | {name}:{function}:{line}"

logger.add(sys.stdout, colorize=True, format=log_format, level="DEBUG")
logger.add("logs/debug.log", rotation="10MB", retention="30 days", level="DEBUG", format=log_format, enqueue=True)
logger.add("logs/info.log", rotation="10MB", retention="30 days", level="INFO", format=log_format, enqueue=True)
logger.add("logs/error.log", rotation="10MB", retention="30 days", level="ERROR", format=log_format, enqueue=True)



# logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")

if __name__ == "__main__":
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
