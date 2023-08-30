import getopt
import logging
import os
from time import sleep
import dotenv
import sys
from common import logging_config, config_reader
from services import main_service
from jobs import job_scheduler_factory


def main():
    # STEP 1: get app base dir
    dir_of_src = os.path.abspath(os.path.dirname(__file__))
    app_base_dir = os.path.dirname(dir_of_src)

    # --------------------------------------------------
    # STEP 2: configure logging and reads env vars to infer env
    logger = logging_config.configure_logging(f"{app_base_dir}/logs/citadel-idp-backend.log")
    logger.info("App base directory inferred as '%s'", app_base_dir)
    app_env = os.environ.get("APP_ENV")
    if not app_env:
        app_env = "local"
        logger.warning("No APP_ENV env variable found. Defaulting to 'local'")
    else:
        logger.info("APP_ENV inferred from environment variable as %s", app_env)

    # --------------------------------------------------
    # STEP 3: read app config
    dot_env_file_path = app_base_dir + "/config-files/" + app_env + "/.env"
    dotenv.load_dotenv(dot_env_file_path)
    config_reader.read_config(app_env, app_base_dir)

    # --------------------------------------------------
    # STEP 4: schedule jobs
    app_jobs_scheduler = job_scheduler_factory.collect_and_schedule_jobs()

    logger.info("App bootstrap completed successfully.")
    # Runs an infinite loop

    try:
        while True:
            sleep(2)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Received app shutdown request. Performing graceful scheduler shutdown.")
        app_jobs_scheduler.shutdown(wait=True)

    logger.info("App shutdown completed successfully.")


if __name__ == "__main__":
    main()
