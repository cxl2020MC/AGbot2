import logging
import logging.handlers
import os

from rich.logging import RichHandler

logger = logging.getLogger("AGbot2")

console_format = "{message}"
file_format = "{asctime} - {levelname:<8} | {message} | {module}:{lineno} ({funcName}, {taskName})"

console_handler = RichHandler(
    rich_tracebacks=True,
    tracebacks_show_locals=True,
    markup=True,
    log_time_format="[%Y-%m-%d %H:%M:%S]",
)
# console_handler.setLevel(logging.DEBUG)

console_docker_handler = logging.StreamHandler(
)
# console_docker_handler.setLevel(logging.DEBUG)
console_docker_handler.setFormatter(logging.Formatter(console_format, style="{"))

file_debug_handler = logging.handlers.TimedRotatingFileHandler(
    "logs/debug.log", when="midnight", interval=1, backupCount=30, encoding="utf-8"
)
file_debug_handler.setLevel(logging.DEBUG)
file_debug_handler.setFormatter(logging.Formatter(file_format, style="{"))

file_info_handler = logging.handlers.TimedRotatingFileHandler(
    "logs/info.log", when="midnight", interval=1, backupCount=30, encoding="utf-8"
)
file_info_handler.setLevel(logging.INFO)
file_info_handler.setFormatter(logging.Formatter(file_format, style="{"))

file_error_handler = logging.handlers.TimedRotatingFileHandler(
    "logs/error.log", when="midnight", interval=1, backupCount=30, encoding="utf-8"
)
file_error_handler.setLevel(logging.ERROR)
file_error_handler.setFormatter(logging.Formatter(file_format, style="{"))

# logging.basicConfig(
#     style="{",
#     level=logging.NOTSET,
#     format=console_format,
#     handlers=[
#         # logging.StreamHandler()
#         console_handler,
#         file_debug_handler,
#         file_info_handler
#     ],
# )

# logging.getLogger("httpcore2").setLevel(logging.INFO)
# logger = logging.getLogger("AGbot2")

logger.setLevel(logging.DEBUG)
# logger.propagate = False

if not os.getenv("RUN_DOCKER"):
    logger.addHandler(console_handler)
else:
    logger.addHandler(console_docker_handler)
logger.addHandler(file_debug_handler)
logger.addHandler(file_info_handler)
logger.addHandler(file_error_handler)


if __name__ == "__main__":
    # logger = logging.getLogger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
