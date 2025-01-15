import os

from unittest.mock import patch

from django.urls import reverse
from django.conf import settings
from django.test import TestCase
from django.test import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile

from app.views import upload_schedule
from app.models import UploadedFileStatus


class UploadScheduleTest(TestCase):
    @patch('app.views.process_schedule_file.delay')
    def test_upload_schedule(self, mock_process_schedule_file):
        # Create a test file
        file = SimpleUploadedFile(
            'schedule.xlsx',
            b'file_content',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # Create a test request
        request = RequestFactory().post('/upload-schedule/', {'schedule_file': file})

        # Call the view function
        response = upload_schedule(request)

        # Assert the response
        expected_url = reverse('app:upload_status', args=[1])
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

        # Assert the status record
        status = UploadedFileStatus.objects.get(id=1)
        self.assertEqual(status.file_path, os.path.join(settings.MEDIA_ROOT, 'schedule.xlsx'))
        self.assertEqual(status.status, 'Pending')

        # Assert the Celery task
        mock_process_schedule_file.assert_called_with(1)

        # Clean up the test file
        os.remove(status.file_path)
