"""
All data objects declared here.
"""

from common import config_reader, utils
from common.custom_exceptions import CitadelIDPProcessingException


class Metadata(object):
    """
    Metadata, represents metadata attributes for the blob.
    """

    status: str = None
    name: str = None
    url: str = None
    blob_type: str = None
    container: str = None
    last_modified: str = None
    created: str = None
    content_md5: str = None
    content_length: int = None
    content_type: str = None

    def __repr__(self):
        return (
            "\n"
            + f"Status='{self.status}'"
            + f"\nblob_path='{self.name}'"
            + f"\nblob_url='{self.url}'"
            + f"\nblob_type='{self.blob_type}'"
            + f"\ncontainer_name='{self.container}'"
            + f"\nlast_modified='{self.last_modified}'"
            + f"\ncreatedOn='{self.created}'"
            + f"\ncontentMD5='{self.content_md5}'"
            + f"\ncontent_length_bytes='{self.content_length}'"
            + f"\ncontent_type='{self.content_type}'"
        )


class InputBlob(object):
    """
    InputBlob represents the input blob that needs to be analyzed.

    Raises :py:class:`CitadelIDPProcessingException` if validation_successful_document_url
    is provided to constructor

    """

    validation_successful_blob_path: str = None
    inprogress_blob_path: str = None
    inprogress_blob_url: str = None
    inprogress_blob_path: str = None
    blob_type: str = None
    form_recognizer_model_id: str = None

    form_recognizer_endpoint: str = None
    # is_processed mean analysis was completed.
    is_processed: bool = False
    # is_successful mean analysis was completed AND processing was successful
    is_successful: bool = False
    # is_successful mean analysis was completed AND processing failed
    is_failed: bool = False

    failed_blob_path: str = None
    successful_blob_path: str = None

    result_json_data: str = None
    meta: str = None

    # --------------------------------------------------------------------------------

    def __init__(
        self,
        blob_type,
        form_recognizer_model_id,
        validation_successful_blob_path=None,
        form_recognizer_endpoint=None,
    ):
        self.blob_type = blob_type
        self.form_recognizer_model_id = form_recognizer_model_id
        if utils.string_is_not_empty(validation_successful_blob_path):
            # validation_successful_blob_path needs to be present
            self.validation_successful_blob_path = validation_successful_blob_path
        else:
            # raise exception
            raise CitadelIDPProcessingException(
                "To create an InputBlob validation_successful_blob_path is required, but none was provided."
            )

        # if no custom form_recognizer_endpoint provided, use the main one in config.
        if form_recognizer_endpoint is None:
            self.form_recognizer_endpoint = config_reader.config_data.get("Main", "form-recognizer-endpoint")
        else:
            self.form_recognizer_endpoint = form_recognizer_endpoint

    def __repr__(self):
        return (
            "\nInputBlob("
            + f"\nvalidation_successful_blob_path='{self.validation_successful_blob_path}'"
            + f"\ninprogress_blob_path='{self.inprogress_blob_path}'"
            + f"\ninprogress_blob_sas_url='{self.inprogress_blob_url}'"
            + f"\nblob_type='{self.blob_type}'"
            + f"\nform_recognizer_model_id='{self.form_recognizer_model_id}'"
            + f"\nform_recognizer_endpoint='{self.form_recognizer_endpoint}'"
            + f"\nis_processed='{self.is_processed}'"
            + f"\nis_successful='{self.is_successful}'"
            + f"\nis_failed='{self.is_failed}'"
            + f"\nsuccessful_blob_path='{self.successful_blob_path}'"
            + f"\nfailed_blob_path='{self.failed_blob_path}'"
            + f"\nresult_json_data='{self.result_json_data}'"
            + ")"
            + f"\n\nMetaData: {self.meta}\n"
        )
