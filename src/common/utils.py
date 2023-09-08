import logging
import os
import base64
import mongoengine as me
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from common import config_reader, constants
from common.data_objects import Metadata
from common.custom_exceptions import (
    MissingDocumentTypeException,
    MissingConfigException,
    ContainerMissingException,
)


def string_is_not_empty(input_str):
    return str is not None and len(input_str) > 0


def is_env_local():
    if config_reader.config_data.has_option("Main", "env"):
        env = config_reader.config_data.get("Main", "env")
    else:
        env = "local"

    return env.lower() == "local".lower()


def is_env_prod():
    if config_reader.config_data.has_option("Main", "env"):
        env = config_reader.config_data.get("Main", "env")
    else:
        env = "prod"

    return env.lower() == "local".lower()


def get_document_type_from_file_name(file_path: str):
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


def get_blob_storage_connection_string() -> str:
    """
    get_blob_storage_connection_string normalizes connection string

    Raises:
        MissingConfigException: Raised if azure-storage-account-connection-str is missing in config file
        MissingConfigException: Raised if azure-storage-account-connection-str is empty in config file

    Returns:
        str : normalized connection string
    """

    if not config_reader.config_data.has_option("Main", "azure-storage-account-connection-str"):
        raise MissingConfigException("Main.azure-storage-account-connection-str is missing in config.")

    connection_string = config_reader.config_data.get("Main", "azure-storage-account-connection-str")

    if not string_is_not_empty(connection_string):
        raise MissingConfigException("Main.azure-storage-account-connection-str is present but has empty value.")

    if connection_string.startswith(("'", '"')) and connection_string.endswith(("'", '"')):
        connection_string = connection_string.strip("'\"")

    return connection_string


def configure_database():
    if not config_reader.config_data.has_option("Main", "mongodb_connection_string"):
        raise MissingConfigException("Main.mongodb_connection_string is missing in config.")

    mongodb_connection_string = config_reader.config_data.get("Main", "mongodb_connection_string")

    if not string_is_not_empty(mongodb_connection_string):
        raise MissingConfigException("Main.mongodb_connection_string is present but has empty value.")

    if mongodb_connection_string.startswith(("'", '"')) and mongodb_connection_string.endswith(("'", '"')):
        mongodb_connection_string = mongodb_connection_string.strip("'\"")

    me.connect(
        host=mongodb_connection_string,
        alias=constants.MONGODB_CONN_ALIAS,
    )


def get_azure_storage_blob_service_client():
    """
    blob_service_client calls BobServiceClient

    Returns:
        BobServiceClient
    """
    return BlobServiceClient.from_connection_string(get_blob_storage_connection_string())


def get_azure_container_client(container_name: str):
    """
    container_client calls ContainerClient

    Args:
        container_name (str): name of container for which you need container client_

    Raises:
        ContainerMissingException: raised when container dosen't exists

    Returns:
        ContainerClient: container client
    """
    container_client = get_azure_storage_blob_service_client().get_container_client(container_name)
    if not container_client.exists():
        raise ContainerMissingException(f"Container '{container_name}' does not exist.")
    else:
        return container_client


def move_blob(source_blob_path: str, source_folder: str, destination_folder: str):
    """
    Moves blob from source folder to destination folder.

    Args:
        source_blob_path (str): path of blob in source folder
        source_folder (str): source folder name
        destination_folder (str): destination folder name.
    """

    destination_blob_path = source_blob_path.replace(source_folder, destination_folder)

    source_blob_client = get_azure_container_client(constants.DEFAULT_BLOB_CONTAINER).get_blob_client(
        blob=source_blob_path
    )
    destination_blob_client = get_azure_container_client(constants.DEFAULT_BLOB_CONTAINER).get_blob_client(
        blob=destination_blob_path
    )

    destination_blob_client.start_copy_from_url(source_blob_client.url)
    source_blob_client.delete_blob()


def get_sas_url(blob_path: str, blob_service_client: BlobServiceClient):
    """
    get_sas_url takes a blob_path and generates sas_url for that blob.

    Args:
        blob_path (str): path of blob.

    Returns:
        returs sas_url of the blob.
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


def get_metadata(status: str, path: str) -> Metadata:
    """
    get_meta takes file status and its path and collects metadata properties of that blob.

    Args:
        status (str): Blob status
        path (str): Path of blob
    Returns:
      str:  returns object of class Metadata
    """
    blob_client = get_azure_container_client(constants.DEFAULT_BLOB_CONTAINER).get_blob_client(path)
    properties = blob_client.get_blob_properties()

    metadata = Metadata()

    metadata.status = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}-{status}]"
    metadata.name = properties.name
    metadata.content_md5 = base64.b64encode(properties.content_settings.content_md5).decode("utf-8")
    metadata.url = blob_client.url
    metadata.blob_type = properties.blob_type
    metadata.container = get_azure_container_client(constants.DEFAULT_BLOB_CONTAINER).container_name
    metadata.content_length = properties.size
    metadata.created = properties.creation_time.strftime("%Y-%m-%d %H:%M:%S")
    metadata.last_modified = properties.last_modified.strftime("%Y-%m-%d %H:%M:%S")
    metadata.content_type = properties.content_settings.content_type

    return metadata
