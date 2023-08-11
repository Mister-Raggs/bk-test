import logging

from common import config_reader
from common.custom_exceptions import FolderMissingBusinessException, CitadelIDPProcessingException
from services import blob_handler


def start_flow():
    logging.info("Starting main app flow....")

    if config_reader.config_data.has_option("Main", "env"):
        env = config_reader.config_data.get("Main", "env")
    else:
        env = "local"

    logging.info("Environment is set as '%s'", env)
    processed_files_list = []

    if env.lower() == "local" or env.lower() == "prod":
        use_azure_blog_storage = True
        if config_reader.config_data.has_option("Main", "use-azure-blog-storage"):
            use_azure_blog_storage = config_reader.config_data.getboolean("Main", "use-azure-blog-storage")

        if use_azure_blog_storage:
            try:
                processed_files_list = blob_handler.check_and_process_blob_storage()
            except FolderMissingBusinessException as fmbe:
                raise CitadelIDPProcessingException(fmbe) from fmbe
            except Exception as ex:
                raise CitadelIDPProcessingException(ex) from ex
        else:
            logging.exception("If env is local or prod use-azure-blog-storage needs to be true")

    # Just logging the details here for now.
    logging.info("Final processing status dump....")
    for processed_file in processed_files_list:
        logging.info("Processed file info is: %s", processed_file)
