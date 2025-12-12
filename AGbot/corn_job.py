import threading
import time

import schedule


def run(interval=1):
    while True:
        schedule.run_pending()
        time.sleep(interval)

def background_run(interval=1):
    threading.Thread(target=run, kwargs={"interval": interval}, name="schedule", daemon=True).start()


def background_job():
    print('Hello from the background thread')


# schedule.every().second.do(background_job)