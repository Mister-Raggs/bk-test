"""
input_blob handler module for reading and writing mongodb and azure blob storage
"""
import logging
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from common import constants, utils
from common.custom_exceptions import (
    MissingConfigException,
    NoInputBlobsForProcessingException,
    CitadelIDPBackendException,
)

from services.input_blob_analysis_service import analyze_blob
from models.input_blob_model import InputBlob, LifecycleStatus, LifecycleStatusTypes


def handle_input_blob_process() -> list[InputBlob]:
    """
    Checks and processes the input_blob.

    Returns:
        list[InputBlob]: List of processed input blobs.
    """
    blob_service_client = utils.get_azure_storage_blob_service_client()
    processed_blobs_list: list[InputBlob] = []

    # Getting list of input_blobs from mongodb that are to be processed
    input_blob_list = get_list_of_input_blobs_from_mongodb(blob_service_client)

    for input_blob in input_blob_list:
        try:
            logging.info("Starting analysis for '%s' ....", input_blob.in_progress_blob_path)
            # start analyze the input blob
            processed_blob = analyze_blob(input_blob, blob_service_client)
            processed_blobs_list.append(processed_blob)
            logging.info("Analysis completed successfully for '%s' ....", input_blob.in_progress_blob_path)
            # update feilds of analyzed input blob in mongodb and move to success folder in azure storage
            input_blob = set_processing_status_and_move_completed_blobs(input_blob, False)

        except MissingConfigException:
            logging.exception(
                "A Missing Config error occurred while analyzing the input_blob '%s'.",
                input_blob.in_progress_blob_path,
            )
            # set feilds of processed input blob in monogdb
            input_blob.is_processed_for_data = True
            processed_lifecycle_status = LifecycleStatus(
                status=LifecycleStatusTypes.PROCESSED,
                message="Blob processed successfully",
                updated_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            input_blob.lifecycle_status_list.append(processed_lifecycle_status)
            input_blob.save()
            # update feilds of analyzed input blob in mongodb and move the blob to failed folder in azure storage
            input_blob = set_processing_status_and_move_completed_blobs(input_blob, True)

            processed_blobs_list.append(input_blob)

        except CitadelIDPBackendException:
            logging.exception(
                "A General Citadel IDP processing error occured while analyzing the document '%s'.",
                input_blob.in_progress_blob_path,
            )
            # set feilds of processed input blob in monogdb
            input_blob.is_processed_for_data = True
            processed_lifecycle_status = LifecycleStatus(
                status=LifecycleStatusTypes.PROCESSED,
                message="Blob processed successfully",
                updated_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            input_blob.lifecycle_status_list.append(processed_lifecycle_status)
            input_blob.save()
            # update feilds of analyzed input blob in mongodb and move the blob to failed folder in azure storage
            input_blob = set_processing_status_and_move_completed_blobs(blob_service_client, input_blob, True)
            processed_blobs_list.append(input_blob)

        except Exception:
            logging.exception(
                "An error occurred while analyzing the input_blob '%s'.", input_blob.in_progress_blob_path
            )
            # set feilds of processed input blob in monogdb
            input_blob.is_processed_for_data = True
            processed_lifecycle_status = LifecycleStatus(
                status=LifecycleStatusTypes.PROCESSED,
                message="Blob processed successfully",
                updated_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            input_blob.lifecycle_status_list.append(processed_lifecycle_status)
            input_blob.save()
            # update feilds of analyzed input blob in mongodb and move the blob to failed folder in azure storage
            input_blob = set_processing_status_and_move_completed_blobs(blob_service_client, input_blob, True)
            processed_blobs_list.append(input_blob)

    return processed_blobs_list


def get_list_of_input_blobs_from_mongodb(blob_service_client: BlobServiceClient) -> list[InputBlob]:
    """
    gets list 'input_input_blob_blobs' from mongodb where is_validation_successful=true and is_processing_for_data = false.

    Raises:
        NoInputBlobsForProcessingException: Raised when no input_blobs are found in mongodb for processing.

    Returns:
        list[InputBlob]: input_blob_list

    """
    updated_input_blobs_list = []

    # TODO: Add datetime check

    # Collecting all the input_blobs from mongodb that are to be processed.
    input_blobs_list: list[InputBlob] = InputBlob.objects(is_validation_successful=True, is_processing_for_data=False)
    if len(input_blobs_list) == 0:
        raise NoInputBlobsForProcessingException(f"Zero input_blobs found in mongodb for processing")

    logging.info("%s input_blobs found in mongodb", len(input_blobs_list))

    for input_blob in input_blobs_list:
        updated_input_blobs_list.append(update_input_blob(input_blob, blob_service_client))

    return updated_input_blobs_list


def update_input_blob(input_blob: InputBlob, blob_service_client: BlobServiceClient) -> InputBlob:
    """
    update_input_blob updates fields in mongodb

    Args:
        input_blob (InputBlob): _description_
        blob_service_client (BlobServiceClient): _description_

    Returns:
        InputBlob: _description_
    """
    # Updating lifecycle_status in mongodb
    processing_lifecycle_status = LifecycleStatus(
        status=LifecycleStatusTypes.PROCESSING,
        message="Strating blob process",
        updated_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    input_blob.lifecycle_status_list.append(processing_lifecycle_status)

    # Updating InputBlob fields in mongodb
    input_blob.blob_type, input_blob.form_recognizer_model_id = utils.get_document_type_from_file_name(
        input_blob.validation_successful_blob_path
    )

    input_blob.in_progress_blob_path = input_blob.validation_successful_blob_path.replace(
        constants.VALIDATION_SUCCESSFUL_SUBFOLDER, constants.INPROGRESS_SUBFOLDER
    )

    input_blob.save()

    logging.info(
        "Moving blob: %s from %s to %s folder in azure blob storage",
        input_blob.validation_successful_blob_path,
        constants.VALIDATION_SUCCESSFUL_SUBFOLDER,
        constants.INPROGRESS_SUBFOLDER,
    )

    # Moving the blob from validation-successful folder to inprogress folder in azure_blob_storage
    move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
        blob_service_client, input_blob.validation_successful_blob_path, input_blob.in_progress_blob_path
    )
    logging.info("Blob moved Successfully")

    # Updating the processing status in Mongodb
    input_blob.is_processing_for_data = True
    input_blob.in_progress_blob_sas_url = get_sas_url(input_blob.in_progress_blob_path, blob_service_client)
    input_blob.save()

    return input_blob


def move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
    blob_service_client: BlobServiceClient, source_blob_path: str, destination_blob_path: str
):
    source_blob_client = blob_service_client.get_blob_client(
        container=constants.DEFAULT_BLOB_CONTAINER, blob=source_blob_path
    )

    destination_blob_client = blob_service_client.get_blob_client(
        container=constants.DEFAULT_BLOB_CONTAINER, blob=destination_blob_path
    )

    destination_blob_client.start_copy_from_url(source_blob_client.url)
    source_blob_client.delete_blob()


def get_sas_url(blob_path: str, blob_service_client: BlobServiceClient) -> str:
    """
    get_sas_url takes a blob_path and generates sas_url for that blob.

    Args:
        blob_path (str): path of blob in azure blob storage
        blob_service_client (BlobServiceClient):

    Returns:
        sas_url (str): returs sas_url of the blob.
    """

    account_name = blob_service_client.get_container_client(constants.DEFAULT_BLOB_CONTAINER).account_name

    sas_token = generate_blob_sas(
        account_name,
        constants.DEFAULT_BLOB_CONTAINER,
        blob_path,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1),
    )

    # Constructing the full SAS URL for the blob
    sas_url = f"https://{account_name}.blob.core.windows.net/{constants.DEFAULT_BLOB_CONTAINER}/{blob_path}?{sas_token}"

    return sas_url


def set_processing_status_and_move_completed_blobs(
    blob_service_client: BlobServiceClient, input_blob: InputBlob, is_error: bool
) -> InputBlob:
    """
    Sets the processing status and moves the completed blobs to appropriate subfolders.

    Args:
        input_blob (InputBlob): The input blob.
        is_error (bool): True if an error occurred during analyzing.

    Returns:
        sas_url (str): returs sas_url of the blob.
    """

    if is_error:
        logging.info("Moving blob '%s' to Failed folder.", input_blob.in_progress_blob_path)
        input_blob.failed_blob_path = input_blob.in_progress_blob_path.replace(
            constants.INPROGRESS_SUBFOLDER, constants.FAILED_SUBFOLDER
        )
        input_blob.save()

        move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
            blob_service_client, input_blob.in_progress_blob_path, input_blob.failed_blob_path
        )

        input_blob.is_processed_success = False
        input_blob.is_processed_failed = True

        processed_and_failed_lifecycle_status = LifecycleStatus(
            status=LifecycleStatusTypes.FAILED,
            message="Blob moved to Failed folder in azure blob storage",
            updated_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        input_blob.lifecycle_status_list.append(processed_and_failed_lifecycle_status)
        input_blob.save()

        return input_blob

    else:
        logging.info("Moving blob '%s' to Successful folder.", input_blob.in_progress_blob_path)
        input_blob.success_blob_path = input_blob.in_progress_blob_path.replace(
            constants.INPROGRESS_SUBFOLDER, constants.SUCCESSFUL_SUBFOLDER
        )
        input_blob.save()

        move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
            blob_service_client, input_blob.in_progress_blob_path, input_blob.success_blob_path
        )

        input_blob.is_processed_success = True
        input_blob.is_processed_failed = False

        processed_and_success_lifecycle_status = LifecycleStatus(
            status=LifecycleStatusTypes.SUCCESS,
            message="Blob moved to Successful folder in azure blob storage",
            updated_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        input_blob.lifecycle_status_list.append(processed_and_success_lifecycle_status)
        input_blob.save()

        return input_blob
