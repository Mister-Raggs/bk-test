import logging
import os
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from common import config_reader, constants
from common.custom_exceptions import MissingDocumentTypeException, MissingConfigException


def string_is_not_empty(input_str):
    return str is not None and len(input_str) > 0


def is_env_local():
    if config_reader.config_data.has_option("Main", "env"):
        env = config_reader.config_data.get("Main", "env")
    else:
        env = "local"

    return env.lower() == "local".lower()


def get_document_type_from_file_name(file_path):
    """
    get_document_type_from_file_name Takes a filename or absolute path and extracts the
    document type form the last part of the base filename.

    e.g file_path = "/Users/xyz/Citadel-IDP-App/local-blob-storage/test-company/VALIDATION-SUCCESSFUL/1001-receipt.jpg" OR

    file_path = "../VALIDATION-SUCCESSFUL/1001-receipt.jpg" OR

    file_path = "1001-receipt.jpg"

    Should extract "receipt" as the result. Using this value as key in config, finds the
    corresponding form recognizer model for this file.

    Args:
        file_path (str): the filename or path to extract the info from.

    Raises:
        MissingDocumentTypeException: Raised if the document type cannot be inferred from the provided file_path
        or there is no form recognizer mapping in config for the inferred document type.

    Returns:
        tuple(str): the first element is the inferred document type and second element is the mapped form recognizer model.
    """

    full_file_name = os.path.basename(file_path)
    name_part = os.path.splitext(full_file_name)[0]
    index = name_part.rfind("-")
    if index == -1:
        # there was no - in the filename part. could be missing there.
        msg = f"File name path {file_path} has no hyphen (-) in it. Was expecting one."
        logging.warning(msg)
        raise MissingDocumentTypeException(msg)

    document_type = name_part[(index + 1) :]
    found = False
    if config_reader.config_data.has_section("Form-Recognizer-Document-Types"):
        for key, value in config_reader.config_data.items("Form-Recognizer-Document-Types"):
            if str(document_type).lower() == str(key).lower():
                return document_type, value

    if not found:
        msg = f"Could not find form recognizer model for document type {document_type} inferred form file name path {file_path}."
        logging.error(msg)
        raise MissingDocumentTypeException(msg)


def connect_str():
    """
    Removes " " from starting and end of the string.

    Return:
        returns connetion string
    """

    if not config_reader.config_data.has_option("Main", "azure-storage-account-connection-str"):
        raise MissingConfigException("Main.azure-storage-account-connection-str is missing in config.")

    azure_storage_account_connection_str = config_reader.config_data.get("Main", "azure-storage-account-connection-str")

    if not string_is_not_empty(azure_storage_account_connection_str):
        raise MissingConfigException("Main.azure-storage-account-connection-str is present but has empty value.")

    if azure_storage_account_connection_str.startswith(("'", '"')) and azure_storage_account_connection_str.endswith(
        ("'", '"')
    ):
        azure_storage_account_connection_str = azure_storage_account_connection_str.strip("'\"")
        return azure_storage_account_connection_str


def move_blob(blob_path: str, destination_folder: str):
    """
    Moves blob from source folder to destination folder.

    Args:
        blob_path (str): path of blob in source folder.
        destination_folder (str): destination folder name.
    """

    # Connectting to the Azure Storage account
    blob_service_client = BlobServiceClient.from_connection_string(connect_str())

    # Getting a reference to the container
    container_client = blob_service_client.get_container_client(constants.DEFAULT_BLOB_CONTAINER)

    # Defining the paths to the source and destination blobs
    source_blob_path = blob_path

    destination_blob_path = source_blob_path.replace(constants.VALIDATION_SUCCESSFUL_SUBFOLDER, destination_folder)

    # Getting a reference to the source blob
    source_blob_client = container_client.get_blob_client(blob=source_blob_path)

    # Getting a reference to the destination blob
    destination_blob_client = container_client.get_blob_client(blob=destination_blob_path)

    # Starting the blob copy operation
    destination_blob_client.start_copy_from_url(source_blob_client.url)

    # Deleting the source blob
    source_blob_client.delete_blob()


def sasurl(blob_path):
    """
    function sasurl takes a blob_path and generates sas_url for that blob.

    Args:
        blob_path (str): path of blob present in inprogress subfolder.

    Returns:
        returs sas_url of the blob.
    """

    container_name = constants.DEFAULT_BLOB_CONTAINER

    blob_service_client = BlobServiceClient.from_connection_string(connect_str())
    container_client = blob_service_client.get_container_client(container_name)

    sas_token = generate_blob_sas(
        container_client.account_name,
        container_name,
        blob_path,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1),
    )

    # Constructing the full SAS URL for the blob
    sas_url = f"https://{container_client.account_name}.blob.core.windows.net/{container_name}/{blob_path}?{sas_token}"
    return sas_url
