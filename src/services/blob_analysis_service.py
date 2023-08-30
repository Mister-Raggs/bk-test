import json
import os
from azure.core.credentials import AzureKeyCredential
from azure.core.serialization import AzureJSONEncoder
from azure.ai.formrecognizer import DocumentAnalysisClient
from common.data_objects import InputBlob
from common import config_reader, utils, constants
from common.custom_exceptions import (
    MissingConfigException,
    CitadelIDPBackendException,
)


def analyze_blob(input_blob: InputBlob) -> InputBlob:
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

    document_analysis_client = DocumentAnalysisClient(
        endpoint=input_blob.form_recognizer_endpoint, credential=AzureKeyCredential(form_recognizer_key)
    )

    poller = None

    if utils.string_is_not_empty(input_blob.inprogress_blob_sas_url):
        poller = document_analysis_client.begin_analyze_document_from_url(
            input_blob.form_recognizer_model_id, input_blob.inprogress_blob_sas_url
        )
    else:
        raise CitadelIDPBackendException("input_blob.inprogress_blob_url should be non empty.")

    result = poller.result()
    result_dict = [result.to_dict()]

    # Creating a dictionary with the blob name and blob output data
    final_result = {
        "input_file_name": os.path.basename(input_blob.inprogress_blob_path),
        "recognizer_result_data": result_dict,
    }

    result_json = json.dumps(final_result, cls=AzureJSONEncoder)

    input_blob.result_json_data = result_json

    destination_path = input_blob.inprogress_blob_path.replace("/Inprogress/", "/")
    json_file_name = f"{destination_path}.json"

    blob_client = utils.container_client(constants.DEFAULT_JSON_OUTPUT_CONTAINER).get_blob_client(json_file_name)
    blob_client.upload_blob(input_blob.result_json_data, overwrite=False)

    return input_blob
