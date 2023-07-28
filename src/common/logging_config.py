import logging


def configure_logging(logFileAbsPath):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)s] - %(message)s",
        handlers=[logging.FileHandler(logFileAbsPath), logging.StreamHandler()],
    )

    # set the azure python sdk logger level to info
    logging.getLogger("azure.core.pipeline.policies").setLevel(logging.WARNING)

    return logging.getLogger(__name__)
