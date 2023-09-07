class CitadelIDPProcessingException(Exception):
    """
    Generic Citadel IDP Exception to be raised for any high level processing failures.
    """


class CitadelIDPBackendException(Exception):
    """
    Generic Citadel IDP Exception to be raised for any high level processing failures.
    """


class FolderMissingBusinessException(CitadelIDPBackendException):
    """
    Exception to be raised when a folder is expected to be present but doesn't exist.
    """


class MissingConfigException(CitadelIDPBackendException):
    """
    Exception to be raised when some config is missing or empty.
    """


class MissingDocumentTypeException(CitadelIDPBackendException):
    """
    Exception to be raised when document type cannot be inferred from file name.
    """


class ContainerMissingException(CitadelIDPBackendException):
    """
    Exception to be raised when a container is expected to be present but doesn't exist.
    """


class BlobMissingException(CitadelIDPBackendException):
    """
    Exception to be raised when blobs are expected to be present but not present.
    """


class JobExecutionException(CitadelIDPBackendException):
    """
    Exception to be raised when a folder is expected to be present but doesn't exist.
    """


class NoInputBlobsForProcessingException(CitadelIDPBackendException):
    """
    Exception to be raised when no documents are found in db for exception.
    """
