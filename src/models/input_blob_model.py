from common import constants
from models.base_model import BaseModel
import mongoengine as me
from enum import Enum
from models.company_model import CompanyModel
from models.user_model import UserModel


class ResultJsonMetaData(me.EmbeddedDocument):
    json_result_container_name = me.StringField()
    json_result_blob_path = me.StringField()


class LifecycleStatusTypes(str, Enum):
    UPLOADED = "UPLOADED"
    INITIAL_VALIDATING = "INITIAL_VALIDATING"
    INITIAL_VALIDATED = "INITIAL_VALIDATED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class LifecycleStatus(me.EmbeddedDocument):
    """
    LifecycleStatus represents a processing lifecycle of this blob

    """

    status = me.EnumField(LifecycleStatusTypes, required=True, default=LifecycleStatusTypes.UPLOADED)
    message = me.StringField(required=True)
    updated_date_time = me.DateTimeField(required=True)

    def __str__(self):
        return (
            "LifecycleStatus("
            + f"status='{self.status}'"
            + f", message='{self.message}'"
            + f", updated_date_time='{self.updated_date_time}'"
            + ")"
        )

    def __repr__(self):
        return "LifecycleStatus(" + f"status='{self.status}'" + f", updated_date_time='{self.updated_date_time}'" + ")"


class MetaData(me.EmbeddedDocument):
    """
    Metadata, represents metadata attributes for the blob.

    """

    blob_type = me.StringField(required=True)
    form_recognizer_model_type = me.StringField(required=True)
    blob_azure_last_modified = me.DateTimeField(required=True)
    blob_azure_created_on = me.DateTimeField(required=True)
    content_md5 = me.StringField(required=True)
    content_length_bytes = me.LongField(required=True)
    content_type = me.StringField(required=True)
    blob_access_tier = me.StringField(required=True)
    blob_lease_state = me.StringField(required=True)
    blob_lease_status = me.StringField(required=True)
    # is the blob stored in azure blob storage with azure managed encryption
    blob_azure_encrypted = me.BooleanField(required=True, default=False)
    # is the blob contents also encrypted with our own encryption
    blob_citadel_encrypted = me.BooleanField(required=True, default=False)

    def __repr__(self):
        return (
            "MetaData("
            + f"form_recognizer_model_type='{self.form_recognizer_model_type}'"
            + f", blob_type='{self.blob_type}'"
            + f", content_length_bytes='{self.content_length_bytes}'"
            + f", content_md5='{self.content_md5}'"
            + ")"
        )

    def __str__(self):
        return (
            "MetaData("
            + f"blob_type='{self.blob_type}'"
            + f"form_recognizer_model_type='{self.form_recognizer_model_type}'"
            + f", blob_azure_last_modified='{self.blob_azure_last_modified}'"
            + f", blob_azure_created_on='{self.blob_azure_created_on}'"
            + f", content_md5='{self.content_md5}'"
            + f", content_length_bytes='{self.content_length_bytes}'"
            + f", content_type='{self.content_type}'"
            + f", blob_access_tier='{self.blob_access_tier}'"
            + f", blob_lease_state='{self.blob_lease_state}'"
            + f", blob_lease_status='{self.blob_lease_status}'"
            + f", blob_azure_encrypted='{self.blob_azure_encrypted}'"
            + f", blob_citadel_encrypted='{self.blob_citadel_encrypted}'"
            + ")"
        )


class InputBlob(BaseModel):
    """
    InputBlob represents the input blob that needs to be analyzed.
    stores the information of movement of file from incomming to validation succesfull

    """

    blob_name = me.StringField(required=True)
    blob_container_name = me.StringField(required=True)
    blob_type = me.StringField()

    incoming_blob_path = me.StringField(required=True)
    incoming_blob_url = me.URLField(required=True)

    validation_failed_blob_path = me.StringField()
    validation_failed_blob_url = me.URLField()

    validation_successful_blob_path = me.StringField()
    validation_successful_blob_url = me.URLField()

    in_progress_blob_path = me.StringField()
    in_progress_blob_sas_url = me.URLField()
    in_progress_blob_url = me.URLField()

    success_blob_path = me.StringField()
    success_blob_url = me.URLField()

    failed_blob_path = me.StringField()
    failed_blob_url = me.URLField()

    # if filed is picked for validation
    is_picked_for_validation = me.BooleanField(required=False, default=False)

    # is_uploaded mean blob is uploaded ot Azure storage.
    is_uploaded = me.BooleanField(required=True, default=True)

    # is_processed_for_validation mean validation check was completed.
    is_processed_for_validation = me.BooleanField(required=True, default=False)

    # is_validation_successful mean if validation was successful or not
    is_validation_successful = me.BooleanField(required=True, default=False)

    # if file is been picked for Analysis
    is_picked_for_analysis = me.BooleanField(required=False, default=False)

    # is_processing_for_data mean backend has moved it to in progress but not processed yet.
    is_processing_for_data = me.BooleanField(required=True, default=False)

    # is_processed_for_data mean backend has processed it or not.
    is_processed_for_data = me.BooleanField(required=True, default=False)

    # is_processed_success mean backend has processed it and moved to success folder.
    is_processed_success = me.BooleanField(required=True, default=False)

    # is_processed_failed mean backend has processed it and moved to failed folder.
    is_processed_failed = me.BooleanField(required=True, default=False)

    uploader_user = me.ReferenceField(UserModel, required=True)
    uploader_company = me.ReferenceField(CompanyModel, required=True)

    is_active = me.BooleanField(required=True, default=True)
    is_deleted = me.BooleanField(required=True, default=False)

    metadata = me.EmbeddedDocumentField(MetaData, required=True)
    lifecycle_status_list = me.ListField(me.EmbeddedDocumentField(LifecycleStatus), required=True)

    json_output = me.EmbeddedDocumentField(ResultJsonMetaData, required=False)
    form_recognizer_model_id = me.StringField()

    meta = {
        "collection": "input_document_blobs",
        "db_alias": constants.MONGODB_CONN_ALIAS,
        "indexes": [
            "blob_name",
            "blob_container_name",
        ],
    }

    # --------------------------------------------------------------------------------
    def __repr__(self):
        uploader_user = f"{self.uploader_user.first_name} {self.uploader_user.last_name} [{str(self.uploader_user.pk)}]"
        uploader_company = f"{self.uploader_company.short_name} [{str(self.uploader_company.pk)}]"
        return (
            "InputBlob("
            + f"_id='{str(self.pk)}'"
            + f", blob_name='{self.blob_name}'"
            + f", blob_container_name='{self.blob_container_name}'"
            + f", uploader_user='{str(self.uploader_user.pk)}'"
            + f", uploader_company='{uploader_company}'"
            + ")"
        )

    def __str__(self):
        uploader_user = f"{self.uploader_user.first_name} {self.uploader_user.last_name} [{str(self.uploader_user.pk)}]"
        uploader_company = f"{self.uploader_company.short_name} [{str(self.uploader_company.pk)}]"
        return (
            "InputBlob("
            + f"_id='{str(self.pk)}'"
            + f", blob_name='{self.blob_name}'"
            + f", blob_container_name='{self.blob_container_name}'"
            + f", blob_type='{self.blob_type}'"
            + f", incoming_blob_path='{self.incoming_blob_path}'"
            + f", incoming_blob_url='{self.incoming_blob_url}'"
            + f", validation_failed_blob_path='{self.validation_failed_blob_path}'"
            + f", validation_failed_blob_url='{self.validation_failed_blob_url}'"
            + f", validation_successful_blob_path='{self.validation_successful_blob_path}'"
            + f", validation_successful_blob_url='{self.validation_successful_blob_url}'"
            + f", in_progress_blob_path='{self.in_progress_blob_path}'"
            + f", in_progress_blob_url='{self.in_progress_blob_url}'"
            + f", in_progress_blob_sas_url='{self.in_progress_blob_sas_url}'"
            + f", form_recognizer_model_id: {self.form_recognizer_model_id}"
            + f", success_blob_path='{self.success_blob_path}'"
            + f", success_blob_url='{self.success_blob_url}'"
            + f", failed_blob_path='{self.failed_blob_path}'"
            + f", failed_blob_url='{self.failed_blob_url}'"
            + f", is_uploaded='{self.is_uploaded}'"
            + f", is_picked_for_validation='{self.is_picked_for_validation}'"
            + f", is_processed_for_validation='{self.is_processed_for_validation}'"
            + f", is_validation_successful='{self.is_validation_successful}'"
            + f", is_picked_for_analysis='{self.is_picked_for_analysis}'"
            + f", is_processing_for_data='{self.is_processing_for_data}'"
            + f", is_processed_for_data='{self.is_processed_for_data}'"
            + f", is_processed_success='{self.is_processed_success}'"
            + f", is_processed_failed='{self.is_processed_failed}'"
            + f", uploader_user='{uploader_user}'"
            + f", uploader_company='{uploader_company}'"
            + f", is_active='{self.is_active}'"
            + f", is_deleted='{self.is_deleted}'"
            + f", date_created='{self.date_created}'"
            + f", date_last_modified='{self.date_last_modified}'"
            + f", metadata: {self.metadata}"
            + f", lifecycle_status_list: '{', '.join([str(e) for e in self.lifecycle_status_list])}'"
            + f", json_output: {self.json_output}"
            + ")"
        )
