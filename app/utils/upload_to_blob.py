import uuid

from app.models import UploadedFileStatus
from config import BLOB_CONN_STR, BLOB_CONTAINER
from azure.storage.blob import BlobServiceClient

import logging
logger = logging.getLogger('app')


def upload_to_blob(file):
    try:
        logger.info("Connecting to Azure Blob Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
        blob_name = f"{uuid.uuid4()}_{file.name}"
        blob_container_client = blob_service_client.get_container_client(BLOB_CONTAINER)
        blob_client = blob_container_client.get_blob_client(blob_name)
        logger.info(f"Uploading blob: {blob_name}")
        blob_client.upload_blob(file, overwrite=True)
        blob_url = blob_client.url

        logger.info(f"File uploaded successfully. Blob URL: {blob_url}")
        return blob_url

    except Exception as e:
        logger.exception("Error uploading to Azure Blob Storage:")
        raise