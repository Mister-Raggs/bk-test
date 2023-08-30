import configparser
import os
import pathlib
import logging

from common import utils, constants, custom_exceptions

config_data = None


class ExtendedEnvInterpolation(configparser.ExtendedInterpolation):
    """Interpolation which expands environment variables in values."""

    def before_get(self, parser, section, option, value, defaults):
        # first try and replace from env vars if needed and they let the base class do its job
        ret_val = os.path.expandvars(value)
        return super().before_get(parser, section, option, ret_val, defaults)


def read_config(env, app_base_dir):
    global config_data
    config = configparser.ConfigParser(interpolation=ExtendedEnvInterpolation())
    config_file_path = app_base_dir + "/config-files/" + env + "/citadel-idp-backend-config.ini"
    if os.path.exists(config_file_path):
        logging.info("Reading app config from - %s", config_file_path)
        config.read(config_file_path)
        config_data = config
    else:
        logging.error(
            "No config file found for env '%s' in the default config folder. Was looking for file '%s'",
            env,
            config_file_path,
        )
        raise custom_exceptions.MissingConfigException()

    # add app_base_dir to config data
    config_data.set("Main", "app_base_dir", app_base_dir)
