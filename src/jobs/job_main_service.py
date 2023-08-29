import schedule
import logging
from datetime import datetime
import time
from services.main_service import start_flow


def my_job():
    start_time = datetime.strptime("08:00:00", "%H:%M:%S")
    end_time = datetime.strptime("23:00:00", "%H:%M:%S")
    now = datetime.now().time()

    if start_time.time() <= now <= end_time.time():
        logging.info("Running scheduled job...")

        try:
            start_flow()
        except Exception as ex:
            logging.exception("An error occured while running the job: %s", (ex))

        logging.info("Job is finished")
    else:
        print(f"Scheduled job only runs between {start_time.time()} and {end_time.time()}")
        exit()


def job_scheduler():
    interval = 15
    schedule.every(interval).seconds.do(my_job)

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error("An error occurred in scheduling:", str(e))
