# To test the configure_logging function using pytest-mock, we can focus on verifying the following scenarios:

# Ensure that the logging level is set to logging.INFO.
# Verify that the logging format is as expected.
# Check if the function sets up both FileHandler and StreamHandler.
# Verify that the logging level for the "azure.core.pipeline.policies" logger is set to logging.WARNING.
# Test if the function returns the correct logger object.

import logging
import pytest
from common.logging_config import configure_logging

def test_configure_logging_level(mocker): 
    mock_basic_config = mocker.patch("logging.basicConfig")
    log_file_path = "C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\logs\\citadel-idp-app.log"
    logger = configure_logging(log_file_path)
    assert mock_basic_config.call_args[1]["level"] == logging.INFO
    assert logger.level == 0 #logging.INFO

def test_configure_logging_format(mocker):
    mock_basic_config = mocker.patch("logging.basicConfig")
    log_file_path = "C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\logs\\citadel-idp-app.log"
    logger = configure_logging(log_file_path)
    expected_format = "%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)s] - %(message)s"
    assert mock_basic_config.call_args[1]["format"] == expected_format

def test_configure_logging_handlers(mocker):
    mock_basic_config = mocker.patch("logging.basicConfig")
    log_file_path = "C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\logs\\citadel-idp-app.log"
    logger = configure_logging(log_file_path)
    handlers = mock_basic_config.call_args[1]["handlers"]
    assert len(handlers) == 2
    assert isinstance(handlers[0], logging.FileHandler)
    assert isinstance(handlers[1], logging.StreamHandler)

def test_configure_logging_azure_logger_level(mocker):
    mock_get_logger = mocker.patch("logging.getLogger")
    mock_set_level = mocker.patch("logging.Logger.setLevel")
    log_file_path = "C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\logs\\citadel-idp-app.log"
    logger = configure_logging(log_file_path)
    assert mock_get_logger.call_args_list[0][0][0] == "azure.core.pipeline.policies"
    assert mock_set_level.call_args[0][0] == logging.WARNING

def test_configure_logging_returns_logger(mocker):
    log_file_path = "C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\logs\\citadel-idp-app.log"
    logger = configure_logging(log_file_path)
    assert isinstance(logger, logging.Logger)
    assert logger.name == __name__
    