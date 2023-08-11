import json
import os

from azure.core.credentials import AzureKeyCredential
from azure.core.serialization import AzureJSONEncoder
from azure.ai.formrecognizer import DocumentAnalysisClient
from common.data_objects import InputBlob
from common import config_reader, utils
from common.custom_exceptions import MissingConfigException, CitadelIDPProcessingException


def analyze_blob(input_blob: InputBlob):
    # TODO: first validate the values in the input document arg are not empty or blanks

    if not config_reader.config_data.has_option("Main", "form-recognizer-key"):
        raise MissingConfigException("Main.form-recognizer-key is missing in config.")

    form_recognizer_key = config_reader.config_data.get("Main", "form-recognizer-key")

    if not utils.string_is_not_empty(form_recognizer_key):
        raise MissingConfigException("Main.form-recognizer-key is present but has empty value.")

    document_analysis_client = DocumentAnalysisClient(
        endpoint=input_blob.form_recognizer_endpoint, credential=AzureKeyCredential(form_recognizer_key)
    )

    poller = None

    if utils.string_is_not_empty(input_blob.inprogress_blob_url):
        poller = document_analysis_client.begin_analyze_document_from_url(
            input_blob.form_recognizer_model_id, input_blob.inprogress_blob_url
        )
    else:
        raise CitadelIDPProcessingException(
            "Since Env is prod was expecting input_document.inprogress_blob_url to be non empty."
        )

    result = poller.result()

    result_dict = [result.to_dict()]
    # Create a dictionary with the file name and receipt data
    final_result = {
        "input_file_name": os.path.basename(input_blob.inprogress_blob_url),
        "recognizer_result_data": result_dict,
    }

    # result_json = json.dumps(final_result, cls=AzureJSONEncoder, indent=2)
    result_json = json.dumps(final_result, cls=AzureJSONEncoder)
    # logging.info("result json is: %s", result_json)
    input_blob.result_json_data = result_json
    return input_blob
