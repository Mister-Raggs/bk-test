"""
All data objects declared here.
"""

import pathlib
from common import config_reader, utils
from common.custom_exceptions import CitadelIDPProcessingException


class InputDocument(object):
    """
    InputDocument represents the input document that needs to be analyzed.

    Raises :py:class:`CitadelIDPProcessingException` if neither validation_successful_local_file_path or validation_successful_document_url
    is provided to constructor

    """

    # if this is a local file then the validation_successful_local_file_path should be filled
    validation_successful_local_file_path = None
    inprogress_local_file_path = None
    is_local = False

    # validation_successful_document_url can be azure storage url or local file:// url. Always use validation_successful_local_file_path to check if document is local file or not.
    validation_successful_document_url = None
    inprogress_document_url = None

    document_type = None
    document_recognizer_model_id = None
    form_recognizer_endpoint = None
    
    # is_processed mean analysis was completed.
    is_processed = False
    
    # is_successful mean analysis was completed AND processing was successful
    is_successful = False
    
    # is_successful mean analysis was completed AND processing failed
    is_failed = False
    
    result_json_data = None

    # --------------------------------------------------------------------------------
    
    def __init__(
        self,
        document_type,
        document_recognizer_model_id,
        validation_successful_local_file_path=None,
        validation_successful_document_url=None,
        form_recognizer_endpoint=None,
    ):
        self.document_type = document_type
        self.document_recognizer_model_id = document_recognizer_model_id
        # either the validation_successful_local_file_path is provided or the validation_successful_document_url is provided
        # if both are missing then raise exception
        if utils.string_is_not_empty(validation_successful_local_file_path):
            self.validation_successful_local_file_path = validation_successful_local_file_path
            self.validation_successful_document_url = pathlib.Path(validation_successful_local_file_path).as_uri()
            self.is_local = True
        elif utils.string_is_not_empty(validation_successful_document_url):
            # validation_successful_document_url needs to be present
            self.validation_successful_document_url = validation_successful_document_url
            self.validation_successful_local_file_path = None
            self.is_local = False
        else:
            # raise exception
            raise CitadelIDPProcessingException(
                "To create an InputDocument one of the validation_successful_local_file_path or the validation_successful_document_url is required, but none were provided."
            )

        # if no custom form_recognizer_endpoint provided, use the main one in config.
        if form_recognizer_endpoint is None:
            self.form_recognizer_endpoint = config_reader.config_data.get("Main", "form-recognizer-endpoint")
        else:
            self.form_recognizer_endpoint = form_recognizer_endpoint

    def __repr__(self):
        return (
            "InputDocument("
            + f"validation_successful_local_file_path='{self.validation_successful_local_file_path}'"
            + f", inprogress_local_file_path='{self.inprogress_local_file_path}'"
            + f", is_local='{self.is_local}'"
            + f", validation_successful_document_url='{self.validation_successful_document_url}'"
            + f", inprogress_document_url='{self.inprogress_document_url}'"
            + f", document_type='{self.document_type}'"
            + f", document_recognizer_model_id='{self.document_recognizer_model_id}'"
            + f", form_recognizer_endpoint='{self.form_recognizer_endpoint}'"
            + f", is_processed='{self.is_processed}'"
            + f", is_successful='{self.is_successful}'"
            + f", is_failed='{self.is_failed}'"
            + f", result_json_data='{self.result_json_data}'"
            + ")"
        )
