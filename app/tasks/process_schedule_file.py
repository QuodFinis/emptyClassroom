import logging
from datetime import time

import pandas as pd
from celery import shared_task
from django.db import transaction
from azure.storage.blob import BlobServiceClient
from config import BLOB_CONN_STR, BLOB_CONTAINER
from app.models import UploadedFileStatus, School, Building, Floor, Room, Department, Course, Professor, Schedule


# TODO: create way so that when UploadedFileStatus table gets a new row it triggers task which is sent to worker uisng that new row
@shared_task
def process_schedule_file(id):
    try:
        # Update file status to "Processing"
        uploaded_file = UploadedFileStatus.objects.get(id=id)
        uploaded_file.status = 'Processing'
        uploaded_file.save()

        # Step 1: Download the file from Azure Blob Storage
        blob_path = UploadedFileStatus.objects.get(id=id).blob_url
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER)
        blob_client = container_client.get_blob_client(blob_path)

        # download file from blob to temp location
        with open("temp.xlsx", "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())

        df = pd.read_excel("temp.xlsx")

        # Step 4: Process Data
        with transaction.atomic():
            for _, row in df.iterrows():
                school, _ = School.objects.get_or_create(school_name=row['school'])
                building, _ = Building.objects.get_or_create(school=school, building_name=row['building'])
                floor, _ = Floor.objects.get_or_create(building=building, floor_number=row['floor'])
                room, _ = Room.objects.get_or_create(floor=floor, room_name=row['room'])
                course, _ = Course.objects.get_or_create(course_name=row['class_name'])

                schedule, created = Schedule.objects.get_or_create(
                    course=course,
                    section=row['section'],
                    room=room,
                    days=row['days'],
                    start_time=time.fromisoformat(row['start_time']),
                    end_time=time.fromisoformat(row['end_time']),
                )

            # Step 5: Update File Status table
            uploaded_file.status = 'Completed'
            uploaded_file.save()

    except Exception as e:
        uploaded_file.status = 'Failed'
        uploaded_file.error_message = str(e)
        uploaded_file.save()
        logging.exception("Error processing schedule file:")
        return {"status": "error", "error": str(e)}

    return {"status": "success", "rows_processed": len(df)}

