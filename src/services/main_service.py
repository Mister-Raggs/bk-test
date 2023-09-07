import logging

from common import config_reader
from common.custom_exceptions import (
    FolderMissingBusinessException,
    CitadelIDPBackendException,
    ContainerMissingException,
    BlobMissingException,
)
from services import input_blob_handler


def start_flow():
    logging.info("Starting main app flow....")

    if config_reader.config_data.has_option("Main", "env"):
        env = config_reader.config_data.get("Main", "env")
    else:
        env = "local"

    logging.info("Environment is set as '%s'", env)
    processed_files_list = []

    if env.lower() == "local" or env.lower() == "prod":
        if config_reader.config_data.has_option("Main", "use-azure-blog-storage"):
            use_azure_blog_storage = config_reader.config_data.getboolean("Main", "use-azure-blog-storage")
        else:
            use_azure_blog_storage = True

        if use_azure_blog_storage:
            try:
                processed_files_list = input_blob_handler.handle_input_blob_process()
            except ContainerMissingException as cme:
                raise CitadelIDPBackendException(cme) from cme
            except BlobMissingException as bme:
                raise CitadelIDPBackendException(bme) from bme
            except FolderMissingBusinessException as fmbe:
                raise CitadelIDPBackendException(fmbe) from fmbe
            except Exception as ex:
                raise CitadelIDPBackendException(ex) from ex
        else:
            logging.exception("If env is local or prod use-azure-blog-storage needs to be true")

    # Just logging the details here for now.
    logging.info("Final processing status dump....")
    for processed_file in processed_files_list:
        logging.info("Processed file info is: %s", processed_file)
