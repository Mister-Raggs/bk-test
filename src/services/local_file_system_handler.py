"""
File handler module for reading and writing to local folders
"""
import os
import shutil
import logging
import pathlib
from glob import iglob

from common import constants, utils
from common.custom_exceptions import (
    FolderMissingBusinessException,
    MissingConfigException,
    CitadelIDPProcessingException,
)
from common.data_objects import InputDocument
from services.document_analysis_service import analyze_document


def check_and_process_local_blob_storage() -> list[InputDocument]:
    """
    Checks and processes the local blob storage folder.

    Returns:
        list[InputDocument]: List of processed input documents.
    Raises:
        FolderMissingBusinessException: Raised if the predefined local blob storage path doesn't exist.
    """
    local_blob_storage_root_folder = (
        pathlib.Path(__file__).parent.absolute() / constants.DEFAULT_LOCAL_BLOB_STORAGE_FOLDER
    )
    # normalize the path...i.e remove any . and .. from the path string
    local_blob_storage_root_folder = os.path.normpath(local_blob_storage_root_folder)
    logging.info("Normalized local blob storage path being used is: %s", local_blob_storage_root_folder)

    if not os.path.exists(local_blob_storage_root_folder):
        raise FolderMissingBusinessException(f"Local blob storage '{local_blob_storage_root_folder}' does not exist.")

    input_documents_list = get_actionable_input_documents_list(local_blob_storage_root_folder)
    processed_files_list: list[InputDocument] = []

    # log an exceptions but dont raise. we need the loop to continue forward and not break out.
    for input_document in input_documents_list:
        try:
            logging.info("Starting analysis for '%s' ....", input_document.inprogress_local_file_path)
            processed_file = analyze_document(input_document)
            processed_files_list.append(processed_file)
            logging.info("Analysis completed successfully for '%s' ....", input_document.inprogress_local_file_path)
            input_document = set_processing_status_and_move_completed_documents(input_document, False)

        except MissingConfigException:
            logging.exception(
                "A Missing Config error occurred while analyzing the document '%s'.", input_document.inprogress_local_file_path
            )
            input_document = set_processing_status_and_move_completed_documents(input_document, True)
            processed_files_list.append(input_document)
        except CitadelIDPProcessingException:
            logging.exception(
                "A General Citadel IDP processing error occured while analyzing the document '%s'.",input_document.inprogress_local_file_path
            )
            input_document = set_processing_status_and_move_completed_documents(input_document, True)
            processed_files_list.append(input_document)
            
        except Exception:
            logging.exception(
                "An error occurred while analyzing the document '%s'.", input_document.inprogress_local_file_path
            )
            input_document = set_processing_status_and_move_completed_documents(input_document, True)
            processed_files_list.append(input_document)

    return processed_files_list


def get_actionable_input_documents_list(source_folder_abs_path: str) -> list[InputDocument]:
    """
    Returns a list of actionable input documents from the provided folder.

    Args:
        source_folder_abs_path (str): The root folder to start the scan from.

    Returns:
        list[InputDocument]: The list of actionable input documents.
    """
    
    # TODO: We need to add logic to ignore files already getting processed or picked. Needs DB integration for that.
    input_documents_list = []
    subfolders = [f.path for f in os.scandir(source_folder_abs_path) if f.is_dir()]

    for dirname in list(subfolders):
        company_folder_name = os.path.basename(dirname)

        if not company_folder_name.startswith(constants.COMPANY_ROOT_FOLDER_PREFIX):
            logging.warning(
                "Folder path '%s' doesn't seem to belong to a company '%s' and doesn't follow the company folder name convention, skipping it.",
                dirname, company_folder_name
            )
            continue

        work_folder = dirname + constants.VALIDATION_SUCCESSFUL_SUBFOLDER

        if not os.path.exists(work_folder):
            logging.error(
                "Was expecting the folder path '%s' to be present but seems it doesn't exist. Skipping parent folder '%s' scanning.",
                constants.VALIDATION_SUCCESSFUL_SUBFOLDER,
                dirname,
            )
        else:
            received_input_documents_list = collect_input_documents(work_folder)

            if len(received_input_documents_list) > 0:
                input_documents_list.extend(received_input_documents_list)

    logging.info("Total actionable files found is %s", len(input_documents_list))
    return input_documents_list


def collect_input_documents(work_folder: str) -> list[InputDocument]:
    """
    Collects the files from the work folder and converts them to `InputDocument` objects.

    Args:
        work_folder (str): The input folder to work on.

    Returns:
        list[InputDocument]: The collected list of input documents.
    """
    input_documents_list: list[InputDocument] = []
    work_folder = work_folder + "/**"
    files_path_list = [f for f in iglob(work_folder, recursive=True) if os.path.isfile(f)]
    logging.info("Found %d files in folder '%s'.", len(files_path_list), work_folder)

    for file_path in files_path_list:
        logging.info("File Path: %s", file_path)
        document_type, form_recognizer_model_id = utils.get_document_type_from_file_name(file_path)
        input_file = InputDocument(document_type, form_recognizer_model_id, file_path)
        # Get an absolute path to inprogress folder for this file path
        inprogress_folder_file_path = file_path.replace(
            constants.VALIDATION_SUCCESSFUL_SUBFOLDER, constants.INPROGRESS_SUBFOLDER
        )
        input_file.inprogress_local_file_path = inprogress_folder_file_path
        input_file.inprogress_document_url = pathlib.Path(inprogress_folder_file_path).as_uri()

        # Move the file to Inprogress folder
        inprogress_folder_path = pathlib.Path(inprogress_folder_file_path).parent

        if not inprogress_folder_path.exists():
            os.makedirs(inprogress_folder_path.absolute())

        shutil.move(file_path, inprogress_folder_file_path)
        
        # Add the document to input docs list
        input_documents_list.append(input_file)

    return input_documents_list


def set_processing_status_and_move_completed_documents(input_document: InputDocument, is_error: bool) -> InputDocument:
    """
    Sets the processing status and moves the completed documents to appropriate subfolders.

    Args:
        input_document (InputDocument): The input document.
        is_error (bool): True if an error occurred during processing.

    Returns:
        InputDocument: The updated input document.
        
    """
    if is_error:
        logging.info("Moving file '%s' to Failed folder.", input_document.inprogress_local_file_path)
        failed_folder_file_path = input_document.inprogress_local_file_path.replace(
            constants.INPROGRESS_SUBFOLDER, constants.FAILED_SUBFOLDER
        )
        failed_folder_path = pathlib.Path(failed_folder_file_path).parent

        if not failed_folder_path.exists():
            os.makedirs(failed_folder_path.absolute())

        shutil.move(input_document.inprogress_local_file_path, failed_folder_file_path)

        input_document.is_processed = True
        input_document.is_successful = False
        input_document.is_failed = True

    else:
        logging.info("Moving file '%s' to Successful folder.", input_document.inprogress_local_file_path)
        successful_folder_file_path = input_document.inprogress_local_file_path.replace(
            constants.INPROGRESS_SUBFOLDER, constants.SUCCESSFUL_SUBFOLDER
        )
        successful_folder_path = pathlib.Path(successful_folder_file_path).parent

        if not successful_folder_path.exists():
            os.makedirs(successful_folder_path.absolute())

        shutil.move(input_document.inprogress_local_file_path, successful_folder_file_path)

        input_document.is_processed = True
        input_document.is_successful = True
        input_document.is_failed = False
        
    return input_document
