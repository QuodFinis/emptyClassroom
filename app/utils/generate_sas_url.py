import datetime

from azure.storage.blob import BlobServiceClient, generate_container_sas, ContainerSasPermissions

from config import BLOB_CONN_STR, BLOB_CONTAINER


def generate_sas_url():
    # Create a SAS token that is valid for 6 minutes
    start_time = datetime.datetime.now(datetime.timezone.utc)
    expiry_time = start_time + datetime.timedelta(minutes=1)

    blob_container_client = BlobServiceClient.from_connection_string(BLOB_CONN_STR)

    sas_token = generate_container_sas(
        account_name=blob_container_client.account_name,
        container_name=BLOB_CONTAINER,
        account_key=blob_container_client.credential.account_key,
        permission=ContainerSasPermissions(read=False, write=True, delete=False, list=False),
        expiry=expiry_time
    )

    sas_url = f"{blob_container_client.url}/{BLOB_CONTAINER}?{sas_token}"

    return sas_url