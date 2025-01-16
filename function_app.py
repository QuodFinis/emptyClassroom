import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

@app.function_name(name='BlobTrigger_ValidateSchedule')
@app.blob_trigger(arg_name="myblob", path="devemptyclassroom/dev-uploaded-files",
                               connection="devemptyclassroom_STORAGE") 
def validate_schedule_file(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob"
                f"Name: {myblob.name}"
                f"Blob Size: {myblob.length} bytes")

    # update UploadFileStatus table in sql database to 'Processing' using the blob url
    
    # validate file is excel, else update UploadFileStatus table in sql database to 'Failed' and include error message stating file is not excel 

    # validate file is less than 5MB, else update UploadFileStatus table in sql database to 'Failed' and include error message stating file is greater than 5MB
    
    # validate file has data, else update UploadFileStatus table in sql database to 'Failed' and include error message stating file has no data
    
    # validate file has correct columns, else update UploadFileStatus table in sql database to 'Failed' and include error message stating file has incorrect columns
    
    # validate file has necessary data in required columns, else update UploadFileStatus table in sql database to 'Failed' and include error message stating file has missing data and in which columns
    
    # if all validations pass, trigger another function that will process the data and update the SQL database with the processed data
    
    