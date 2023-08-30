import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR
from pytz import utc

from common.custom_exceptions import JobExecutionException


def scheduler_error_listener(event):
    try:
        job = app_jobs_scheduler.get_job(event.job_id)
        raise JobExecutionException(
            f"An error occurred while executing instance {job.id} of job {job.name}", event.exception
        )
    except:
        logging.exception("Job execution failed.")


# setup the job schedular
job_stores = {
    "default": MemoryJobStore(),
}

executors = {
    "default": ThreadPoolExecutor(10),
    "processpool": ProcessPoolExecutor(3),
}

job_defaults = {
    "coalesce": False,
    "max_instances": 1,
}

app_jobs_scheduler = BackgroundScheduler(
    jobstores=job_stores,
    executors=executors,
    job_defaults=job_defaults,
    timezone=utc,
    daemon=False,
)

# add error listener to the scheduler
app_jobs_scheduler.add_listener(scheduler_error_listener, EVENT_JOB_ERROR)
