"""
Blob handler module for reading and writing azure blob storage
"""
import logging
from azure.storage.blob import BlobServiceClient, ContainerClient

from common import constants, utils
from common.custom_exceptions import (
    FolderMissingBusinessException,
    CitadelIDPProcessingException,
    MissingConfigException,
)

from common.data_objects import InputDocument
from services.document_analysis_service import analyze_document


def check_and_process_blob_storage() -> list[InputDocument]:
    """
    Checks and processes the azure blob storage.

    Returns:
        list[InputDocument]: List of processed input blobs.
    Raises:
        FolderMissingBusinessException: Raised if the predefined azure container doesn't exist.
    """
    blob_container = constants.DEFAULT_BLOB_CONTAINER
    logging.info("%s blob container is being used.", blob_container)

    azure_storage_account_connection_str = utils.connect_str()

    blob_service_client = BlobServiceClient.from_connection_string(azure_storage_account_connection_str)

    # Getting a list of all containers in the storage account
    container_list = blob_service_client.list_containers()
    container_names = [container.name for container in container_list]

    if not blob_container in container_names:
        raise FolderMissingBusinessException(f"azure blob container '{blob_container}' does not exist.")

    input_blobs_list = get_input_blobs_list()
    processed_blobs_list: list[InputDocument] = []

    for input_blob in input_blobs_list:
        try:
            logging.info("Starting analysis for '%s' ....", input_blob.inprogress_local_file_path)
            processed_blob = analyze_document(input_blob)
            processed_blobs_list.append(processed_blob)
            logging.info("Analysis completed successfully for '%s' ....", input_blob.inprogress_local_file_path)
            input_blob = set_processing_status_and_move_completed_blobs(input_blob, False)

        except MissingConfigException:
            logging.exception(
                "A Missing Config error occurred while analyzing the document '%s'.",
                input_blob.inprogress_local_file_path,
            )
            input_blob = set_processing_status_and_move_completed_blobs(input_blob, True)
            processed_blobs_list.append(input_blob)

        except CitadelIDPProcessingException:
            logging.exception(
                "A General Citadel IDP processing error occured while analyzing the document '%s'.",
                input_blob.inprogress_local_file_path,
            )
            input_blob = set_processing_status_and_move_completed_blobs(input_blob, True)
            processed_blobs_list.append(input_blob)

        except Exception:
            logging.exception(
                "An error occurred while analyzing the document '%s'.", input_blob.inprogress_local_file_path
            )
            input_blob = set_processing_status_and_move_completed_blobs(input_blob, True)
            processed_blobs_list.append(input_blob)

    return processed_blobs_list


def get_input_blobs_list() -> list[InputDocument]:
    """
    Returns a list of input blobs from the provided folder.


    Returns:
        list[InputDocument]: The list of actionable input blobs.
    """
    input_blobs_list = []

    container_client = ContainerClient.from_connection_string(utils.connect_str(), constants.DEFAULT_BLOB_CONTAINER)

    subfolders = []
    work_folder_list = []
    for blob in container_client.list_blobs():
        name = blob.name
        parts = name.split("/")
        subfolder = parts[0]
        inner_folder = f"{parts[0]}/{parts[1]}"
        subfolders.append(subfolder)
        work_folder_list.append(inner_folder)

    for company_folder_name in list(subfolders):
        if not company_folder_name.startswith(constants.COMPANY_ROOT_FOLDER_PREFIX):
            logging.warning(
                "Folder name '%s' doesn't seem to belong to a company and doesn't follow the company folder name convention, skipping it.",
                company_folder_name,
            )
            continue

        work_folder = company_folder_name + constants.VALIDATION_SUCCESSFUL_SUBFOLDER

        if not work_folder in work_folder_list:
            logging.error(
                "Was expecting the folder path '%s' to be present but seems it doesn't exist. Skipping parent folder '%s' scanning.",
                constants.VALIDATION_SUCCESSFUL_SUBFOLDER,
                company_folder_name,
            )
        else:
            received_blobs_list = collect_input_blobs(work_folder)

            if len(received_blobs_list) > 0:
                input_blobs_list.extend(received_blobs_list)

    logging.info("Total actionable files found is %s", len(received_blobs_list))
    return input_blobs_list


def collect_input_blobs(work_folder: str) -> list[InputDocument]:
    """
    Collects the sas_url of blobs from the work folder and converts them to `InputDocument` objects.

    Args:
        work_folder (str): The input folder to work on.

    Returns:
        list[InputDocument]: The collected list of input blobs.
    """
    input_blobs_list: list[InputDocument] = []

    container_client = ContainerClient.from_connection_string(utils.connect_str(), constants.DEFAULT_BLOB_CONTAINER)
    blobs = container_client.list_blobs(name_starts_with=work_folder)
    blob_paths = []
    for blob in blobs:
        blob_paths.append(blob.name)

    logging.info("Found %d files in folder '%s'.", len(blob_paths), work_folder)

    for blob_path in blob_paths:
        logging.info("Blob Path: %s", blob_path)
        document_type, form_recognizer_model_id = utils.get_document_type_from_file_name(blob_path)
        input_blob = InputDocument(document_type, form_recognizer_model_id, blob_path)

        # Getting path to inprogress folder for this file path
        inprogress_folder_blob_path = blob_path.replace(
            constants.VALIDATION_SUCCESSFUL_SUBFOLDER, constants.INPROGRESS_SUBFOLDER
        )
        input_blob.inprogress_local_file_path = inprogress_folder_blob_path

        # Moving from validation-successful to inprogress subfolder
        destination_folder = constants.INPROGRESS_SUBFOLDER
        utils.move_blob(blob_path, destination_folder)

        # generating sas_url
        input_blob.inprogress_document_url = utils.sasurl(inprogress_folder_blob_path)
        input_blobs_list.append(input_blob)

    return input_blobs_list


def set_processing_status_and_move_completed_blobs(input_blob: InputDocument, is_error: bool) -> InputDocument:
    """
    Sets the processing status and moves the completed blobs to appropriate subfolders.

    Args:
        input_blob (InputDocument): The input blob.
        is_error (bool): True if an error occurred during processing.

    Returns:
        InputDocument: The updated input blob.

    """
    if is_error:
        logging.info("Moving file '%s' to Failed folder.", input_blob.inprogress_local_file_path)
        destination_folder = constants.FAILED_SUBFOLDER
        utils.move_blob(input_blob.inprogress_local_file_path, destination_folder)
        input_blob.is_processed = True
        input_blob.is_successful = False
        input_blob.is_failed = True

    else:
        logging.info("Moving file '%s' to Successful folder.", input_blob.inprogress_local_file_path)
        destination_folder = constants.SUCCESSFUL_SUBFOLDER
        utils.move_blob(input_blob.inprogress_local_file_path, destination_folder)
        input_blob.is_processed = True
        input_blob.is_successful = True
        input_blob.is_failed = False

    return input_blob
