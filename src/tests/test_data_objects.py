import pytest
import pathlib
from common import config_reader ,utils
from common.custom_exceptions import CitadelIDPProcessingException
from common.data_objects import InputDocument


# Test initialization with local file path
def test_input_document_init_local_path(mocker):
    #modify the data objects class by making the arguments declared with path,type and endpoint and remove the documnet id in the class arguments (__init__)
    validation_successful_local_file_path = "C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\local-blob-storage\\Company-A\\Validation-Successful"
    document_type = "receipt"
    form_recognizer_endpoint = "https://aarkformrecognizer.cognitiveservices.azure.com/"
    # mocker.patch("common.config_reader.config_data.get", return_value=form_recognizer_endpoint)
    input_document = InputDocument()
    assert input_document.validation_successful_local_file_path == validation_successful_local_file_path
    assert input_document.validation_successful_document_url == pathlib.Path(validation_successful_local_file_path).as_uri()
    assert input_document.is_local is True
    assert input_document.document_type == document_type
    # assert input_document.document_recognizer_model_id == document_recognizer_model_id
    assert input_document.form_recognizer_endpoint == form_recognizer_endpoint



def test_input_document_init_document_url(mocker):
    document_type = "Receipt"
    # document_recognizer_model_id = "model-456"
    form_recognizer_endpoint = "https://aarkformrecognizer.cognitiveservices.azure.com/"
    # mocker.patch("common.config_reader.config_data.get", return_value=form_recognizer_endpoint)
    input_document = InputDocument()
    assert input_document.validation_successful_local_file_path is None
    # assert input_document.validation_successful_document_url == validation_successful_document_url
    assert input_document.is_local is False
    assert input_document.document_type == document_type
    # assert input_document.document_recognizer_model_id == document_recognizer_model_id
    assert input_document.form_recognizer_endpoint == form_recognizer_endpoint



def test_input_document_init_both_paths_raises_exception(mocker):
    validation_successful_local_file_path = "C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\local-blob-storage\\Company-B\\Validation-Successful"
    form_recognizer_endpoint = "https://aarkformrecognizer.cognitiveservices.azure.com/"
    document_type = "Invoice4"
    with pytest.raises(CitadelIDPProcessingException):
        InputDocument( document_type,validation_successful_local_file_path,form_recognizer_endpoint)


     
def test_input_document_init_no_path_or_url_raises_exception(mocker):
    document_type = "Invoice"
    # document_recognizer_model_id = "model-123"
    with pytest.raises(CitadelIDPProcessingException):
        InputDocument()



def test_input_document_init_with_custom_endpoint(mocker):
    validation_successful_document_url = "https://example.com/files/file.pdf"
    document_type = "Receipt"
    # document_recognizer_model_id = "model-456"
    custom_endpoint = "https://custom-endpoint.com"
    mocker.patch("common.config_reader.config_data.get", return_value="https://default-endpoint.com")
    input_document = InputDocument()
    assert input_document.form_recognizer_endpoint == custom_endpoint

