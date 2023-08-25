import getopt
import sys
import time
import schedule
from datetime import datetime
from common import logging_config, config_reader
from services import main_service


def main():
    # initialize logging
    args = sys.argv[1:]
    config_file_path = (
        "C:\\Users\\AshishChib\\Documents\\GitHub\\Citadel-IDP-Backend\\config-files\\local\\citadel-idp-config.ini"
    )
    log_file_abs_path = "C:\\Users\\AshishChib\\Documents\\GitHub\\Citadel-IDP-Backend\\logs\\citadel-idp-app.log"

    # reads cmd line args if any
    try:
        opts, args = getopt.getopt(args, "hc:l:", ["help", "config-file-abs-path=", "log-file-abs-path="])
    except getopt.GetoptError:
        print("test.py -c <config file absolute path>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            # TODO: Add usage printing function
            print("Dummy Usage - actual to be added")
            sys.exit()
        elif opt in ("-c", "--config-file-abs-path"):
            config_file_path = arg
        elif opt in ("-l", "--log-file-abs-path"):
            log_file_abs_path = arg

    logger = logging_config.configure_logging(log_file_abs_path)

    logger.info("Reading App config from: %s", config_file_path)
    config_reader.read_config(config_file_path)
    logger.info("App config read successfully.")

    try:
        main_service.start_flow()
    except Exception as ex:
        logger.exception("An error occured while running the app: %s", str(ex))

    logger.info("Finished")


def run_scheduled_task():
    now = datetime.now().time()
    if start_time.time() <= now <= end_time.time():
        print("Running scheduled task...")
        main()


if __name__ == "__main__":
    main()
    start_time = datetime.strptime("08:00:00", "%H:%M:%S")
    end_time = datetime.strptime("23:00:00", "%H:%M:%S")

    schedule.every(15).seconds.do(run_scheduled_task)

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            print("An error occurred in scheduling:", str(e))
