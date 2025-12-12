import threading
import time

import schedule

from .log import logger as log


def run(interval=1):
    while True:
        schedule.run_pending()
        time.sleep(interval)

def background_run(interval=1):
    log.debug("启动后台任务")
    threading.Thread(target=run, kwargs={"interval": interval}, name="schedule", daemon=True).start()
    log.debug("启动后台任务成功")

# def background_job():
#     print('Hello from the background thread')


# schedule.every().second.do(background_job)