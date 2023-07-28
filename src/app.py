import getopt
import sys

from common import logging_config, config_reader
from services import main_service


def main():
    # initialize logging
    args = sys.argv[1:]
    config_file_path = ""
    log_file_abs_path = ""

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
    
    main_service.start_flow()

    logger.info("Finished")


if __name__ == "__main__":
    main()
