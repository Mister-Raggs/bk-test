import pytest
import configparser
import pathlib
from common import utils
from common.config_reader import read_config

# print(utils.string_is_not_empty('sds'))
def test_read_config_with_valid_path(mocker):
    # Mocking the configparser.ConfigParser class and its read method
    mock_configparser = mocker.patch("configparser.ConfigParser")
    mock_configparser.return_value.read = mocker.Mock()
    # Call the function with a valid path
    config_file_path = "C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\config-files\\local\\citadel-idp-config.ini"
    read_config(config_file_path)
    # Assertions
    assert mock_configparser.called
    mock_configparser.return_value.read.assert_called_with(config_file_path)

def test_read_config_with_empty_path(mocker):
    # Mocking the configparser.ConfigParser class and its read method
    mock_configparser = mocker.patch("configparser.ConfigParser")
    mock_configparser.return_value.read = mocker.Mock()
    # Mocking the utils.string_is_not_empty function
    mocker.patch("src.common.utils.string_is_not_empty", return_value=True)
    # Call the function with an empty path
    read_config("")
    # Assertions
    assert mock_configparser.called
    assert mock_configparser.return_value.read.called

def test_read_config_with_default_path(mocker):
    # Mocking the configparser.ConfigParser class and its read method
    mock_configparser = mocker.patch("configparser.ConfigParser")
    mock_configparser.return_value.read = mocker.Mock()
    # Mocking the utils.string_is_not_empty function
    mocker.patch("src.common.utils.string_is_not_empty", return_value=False)
    # Mocking pathlib.Path methods
    # The correct way to mock the pathlib.Path class and its methods is as follows:
    mock_path = mocker.patch("pathlib.Path")
    mock_path.return_value.parent.absolute.return_value = "C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\config-files\\local\\citadel-idp-config.ini"
    # Call the function with an empty path
    read_config("C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\config-files\\local\\citadel-idp-config.ini")
    # Assertions
    assert mock_configparser.called
    mock_configparser.return_value.read.assert_called_with("C:\\Users\\saiki\\OneDrive\\Documents\\Citadel-IDP-Src\\config-files\\local\\citadel-idp-config.ini")
