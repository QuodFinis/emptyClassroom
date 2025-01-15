FROM python:3.11-slim

# Set work directory
WORKDIR /tasks

# Install Python dependencies
COPY requirements.txt .
COPY models.py .
COPY process_schedule_file.py .
RUN pip install --no-cache-dir -r requirements.txt

# Set entry point
ENV DJANGO_SETTINGS_MODULE=your_project.settings
CMD ["celery", "-A", "emptyClassroom", "worker", "--loglevel=info"]