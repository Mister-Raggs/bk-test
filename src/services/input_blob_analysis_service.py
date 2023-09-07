import json
import os
from azure.core.credentials import AzureKeyCredential
from azure.core.serialization import AzureJSONEncoder
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient

from models.input_blob_model import InputBlob, ResultJsonMetaData
from common import config_reader, utils, constants
from common.custom_exceptions import (
    MissingConfigException,
    CitadelIDPBackendException,
)


def analyze_blob(input_blob: InputBlob, blob_service_client: BlobServiceClient) -> InputBlob:
    """
    analyze_blob generates the output for blob

    Args:
        input_blob (InputBlob): Blob that is going to be analyzed by form-recognizer

    Raises:
        MissingConfigException: Raised if form-recognizer-key is missing in config file.
        MissingConfigException: Raised if form-recognizer-key is empty
        CitadelIDPProcessingException:Raised if input_blob.inprogress_blob_url is empty


    Returns:
        InputBlob: The updated input blob
    """
    # TODO: first validate the values in the input blob arg are not empty or blanks
    if not config_reader.config_data.has_option("Main", "form-recognizer-key"):
        raise MissingConfigException("Main.form-recognizer-key is missing in config.")

    form_recognizer_key = config_reader.config_data.get("Main", "form-recognizer-key")

    if not utils.string_is_not_empty(form_recognizer_key):
        raise MissingConfigException("Main.form-recognizer-key is present but has empty value.")

    if not config_reader.config_data.has_option("Main", "form-recognizer-endpoint"):
        raise MissingConfigException("Main.form_recognizer_endpoint is missing in config.")

    form_recognizer_endpoint = config_reader.config_data.get("Main", "form-recognizer-endpoint")

    if not utils.string_is_not_empty(form_recognizer_endpoint):
        raise MissingConfigException("Main.form_recognizer_endpoint is present but has empty value.")

    document_analysis_client = DocumentAnalysisClient(
        form_recognizer_endpoint, credential=AzureKeyCredential(form_recognizer_key)
    )

    input_blob.save()

    poller = None

    if utils.string_is_not_empty(input_blob.in_progress_blob_sas_url):
        poller = document_analysis_client.begin_analyze_document_from_url(
            input_blob.form_recognizer_model_id, input_blob.in_progress_blob_sas_url
        )
    else:
        raise CitadelIDPBackendException("input_blob.in_progress_blob_url should be non empty.")

    result = poller.result()
    result_dict = [result.to_dict()]

    # Creating a dictionary with the blob name and blob output data
    final_result = {
        "input_file_name": os.path.basename(input_blob.in_progress_blob_path),
        "recognizer_result_data": result_dict,
    }

    result_json = json.dumps(final_result, cls=AzureJSONEncoder)

    result_json_path = input_blob.in_progress_blob_path.replace("/Inprogress/", "/")
    result_json_path_in_azure_blob_storage = f"{result_json_path}.json"

    blob_client = blob_service_client.get_blob_client(
        container=constants.DEFAULT_JSON_OUTPUT_CONTAINER, blob=result_json_path_in_azure_blob_storage
    )

    # Uploading the formrecognizer output to azure blob storage
    blob_client.upload_blob(result_json, overwrite=False)

    input_blob.json_output = ResultJsonMetaData(
        json_result_container_name=constants.DEFAULT_JSON_OUTPUT_CONTAINER,
        json_result_blob_path=result_json_path_in_azure_blob_storage,
    )
    input_blob.save()

    return input_blob
