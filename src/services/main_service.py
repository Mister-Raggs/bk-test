import logging

from common import config_reader
from common.custom_exceptions import FolderMissingBusinessException, CitadelIDPProcessingException
from services import local_file_system_handler, azure_blob_handler


def start_flow():
    logging.info("Starting main app flow....")

    if config_reader.config_data.has_option("Main", "env"):
        env = config_reader.config_data.get("Main", "env")
    else:
        env = "local"

    logging.info("Environment is set as '%s'", env)

    processed_files_list = None
    if env.lower() != "prod":
        use_azure_blog_storage = False
        if config_reader.config_data.has_option("Main", "use-azure-blog-storage"):
            use_azure_blog_storage = config_reader.config_data.getboolean("Main", "use-azure-blog-storage")

        if not use_azure_blog_storage:
            try:
                processed_files_list = local_file_system_handler.check_and_process_local_blob_storage()
            except FolderMissingBusinessException as fmbe:
                raise CitadelIDPProcessingException(fmbe) from fmbe
            except Exception as ex:
                raise CitadelIDPProcessingException(ex) from ex
        else:
            # check and process azure blob storage
            logging.info("Dummy msg: Processing Azure blob storage")

    else:
        processed_files_list = azure_blob_handler.check_and_process_blob_storage()

    # Just logging the details here for now.
    logging.info("Final processing status dump....")
    for processed_file in processed_files_list:
        logging.info("Processed file info is: %s", processed_file)
