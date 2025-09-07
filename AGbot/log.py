from loguru import logger
import sys

logger.remove()

log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level.icon} <lvl>{level:<8}</lvl> | {name}:{function}:{line} | {message}"

logger.add(sys.stdout, colorize=True, format=log_format, level="DEBUG")
logger.add("logs/app.log", rotation="50MB", retention="10 days", level="DEBUG", format=log_format, enqueue=True)

# logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")

if __name__ == "__main__":
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
