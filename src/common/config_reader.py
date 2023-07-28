import configparser
import pathlib
import logging

from common import utils, constants

config_data = None


def read_config(configFileAbsPath):
    global config_data
    config = configparser.ConfigParser()
    config_file_path = None
    if utils.string_is_not_empty(configFileAbsPath):
        logging.info("Reading app config from - %s", configFileAbsPath)
        config_file_path = configFileAbsPath
    else:
        logging.warning(
            "No explicit config file path provided. Reading app config from - %s", constants.DEFAULT_CONFIG_FILE_PATH
        )
        config_file_path = pathlib.Path(__file__).parent.absolute() / constants.DEFAULT_CONFIG_FILE_PATH

    config.read(config_file_path)
    config_data = config
