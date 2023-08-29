"""
    This module contains the list of all custom exceptions for Citadel IDP
"""


class CitadelIDPProcessingException(Exception):
    """
    Generic Citadel IDP Exception to be raised for any high level processing failures.
    """


class FolderMissingBusinessException(CitadelIDPProcessingException):
    """
    Exception to be raised when a folder is expected to be present but doesn't exist.
    """


class MissingConfigException(CitadelIDPProcessingException):
    """
    Exception to be raised when some config is missing or empty.
    """


class MissingDocumentTypeException(CitadelIDPProcessingException):
    """
    Exception to be raised when document type cannot be inferred from file name.
    """


class ContainerMissingException(CitadelIDPProcessingException):
    """
    Exception to be raised when a container is expected to be present but doesn't exist.
    """


class BlobMissingException(CitadelIDPProcessingException):
    """
    Exception to be raised when blobs are expected to be present but not present.
    """
