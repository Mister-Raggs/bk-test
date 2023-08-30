from datetime import datetime
import logging
import threading
from time import sleep

SCHEDULE_INTERVAL_IN_SECONDS = 4
JOB_NAME = "JOB-2"


def job_task():
    logging.info(
        "Start - %s, %s - %s sec - Current date and time : %s",
        threading.current_thread().name,
        JOB_NAME,
        SCHEDULE_INTERVAL_IN_SECONDS,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    sleep(3)
    logging.info(
        "Finish - %s, %s - %s sec - Current date and time : %s",
        threading.current_thread().name,
        JOB_NAME,
        SCHEDULE_INTERVAL_IN_SECONDS,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
