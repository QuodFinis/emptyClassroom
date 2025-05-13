import csv
import regex as re
from datetime import datetime
from django.db import transaction
from django.db.utils import IntegrityError
from django.core.management import call_command
from django.core.management.base import BaseCommand
from classrooms.models import (
    ScheduleDump, College, Building,
    Room, Schedule
)


class Command(BaseCommand):
    help = 'Imports schedule data from CSV into ScheduleDump and normalized models'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument(
            '--skip-dump',
            action='store_true',
            help='Skip saving to ScheduleDump model',
        )
        parser.add_argument(
            '--skip-normalized',
            action='store_true',
            help='Skip processing to normalized models',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        total_rows = 0
        processed_rows = 0

        with open(csv_file, 'r') as file:
            reader = csv.DictReader(file)
            total_rows = sum(1 for _ in reader)  # Count total rows
            file.seek(0)  # Reset file pointer
            next(reader)  # Skip header

            self.stdout.write(self.style.SUCCESS(f'Starting import of {total_rows} rows...'))

            with transaction.atomic():
                for i, row in enumerate(reader, 1):
                    try:
                        if not options['skip_dump']:
                            self.import_to_dump(row)

                        if not options['skip_normalized']:
                            self.process_to_normalized(row)

                        processed_rows += 1

                        if i % 100 == 0:  # Progress update every 100 rows
                            self.stdout.write(f'Processed {i}/{total_rows} rows...')

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"Error processing row {i}: {str(e)}. Row data: {row}"
                        ))
                        continue

        self.stdout.write(self.style.SUCCESS(f'Successfully processed {processed_rows}/{total_rows} rows'))

        self.stdout.write(self.style.SUCCESS('Starting availability population...'))
        call_command('populate_availabilities')
        self.stdout.write(self.style.SUCCESS('Availability population complete!'))

    def import_to_dump(self, row):
        """Import raw data into ScheduleDump model"""
        try:
            ScheduleDump.objects.create(
                college_name=row['college_name'].strip(),
                term=row['term'].strip(),
                subject=row['subject'].strip(),
                course_code=row['course_code'].strip(),
                course_name=row['course_name'].strip(),
                building=row['building'].strip(),
                room=row['room'].strip(),
                start_date=self.parse_date(row['start_date']),
                end_date=self.parse_date(row['end_date']),
                days=row['days'].strip(),
                start_time=self.parse_time(row['start_time']),
                end_time=self.parse_time(row['end_time'])
            )
        except IntegrityError:
            self.stdout.write(self.style.WARNING(
                f"Duplicate entry found in ScheduleDump for: {row['course_code']} - {row['days']}"
            ))
        except Exception as e:
            raise Exception(f"Error saving to ScheduleDump: {str(e)}")

    def process_to_normalized(self, row):
        """Process data into normalized models"""
        try:
            # Get or create College
            college, _ = College.objects.get_or_create(
                name=row['college_name'].strip()
            )

            # Get or create Building
            building, _ = Building.objects.get_or_create(
                name=row['building'].strip(),
                college=college
            )

            # Get or create Room
            room, _ = Room.objects.get_or_create(
                name=row['room'].strip(),
                college=college,
                building=building
            )

            # Process each day in the days string
            days = self.parse_days(row['days'])
            if not days:
                self.stdout.write(self.style.WARNING(
                    f"No valid days found for course {row['course_code']}: {row['days']}"
                ))
                return

            start_date = self.parse_date(row['start_date'])
            end_date = self.parse_date(row['end_date'])
            start_time = self.parse_time(row['start_time'])
            end_time = self.parse_time(row['end_time'])

            for day in days:
                Schedule.objects.get_or_create(
                        room=room,
                        day=day,
                        start_time=start_time,
                        end_time=end_time,
                        start_date=start_date,
                        end_date=end_date
                    )

        except Exception as e:
            raise Exception(f"Error processing normalized data: {str(e)}")

    def parse_date(self, date_str):
        """Convert MM/DD/YYYY to date object with validation"""
        try:
            return datetime.strptime(date_str.strip(), '%m/%d/%Y').date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected MM/DD/YYYY")

    def parse_time(self, time_str):
        """Convert HH:MM AM/PM to time object with validation"""
        try:
            time_str = time_str.strip()
            # Handle cases where AM/PM is not separated by space
            time_str_transformed = re.sub(r'(?<=\d)(AM|PM)', r' \1', time_str, flags=re.IGNORECASE)
            return datetime.strptime(time_str_transformed.upper(), '%I:%M %p').time()
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM AM/PM")

    def parse_days(self, days_str):
        """Convert day string to list of standardized day codes"""
        days_str = days_str.strip()
        if not days_str:
            return []

        day_map = {
            'Mo': 'Mo', 'MO': 'Mo', 'Mon': 'Mo', 'Monday': 'Mo',
            'Tu': 'Tu', 'TU': 'Tu', 'Tue': 'Tu', 'Tues': 'Tu', 'Tuesday': 'Tu',
            'We': 'We', 'WE': 'We', 'Wed': 'We', 'Wednesday': 'We',
            'Th': 'Th', 'TH': 'Th', 'Thu': 'Th', 'Thur': 'Th', 'Thursday': 'Th',
            'Fr': 'Fr', 'FR': 'Fr', 'Fri': 'Fr', 'Friday': 'Fr',
            'Sa': 'Sa', 'SA': 'Sa', 'Sat': 'Sa', 'Saturday': 'Sa',
            'Su': 'Su', 'SU': 'Su', 'Sun': 'Su', 'Sunday': 'Su'
        }

        found_days = set()
        i = 0
        n = len(days_str)

        while i < n:
            # Check for 2-character abbreviations first
            if i + 2 <= n and days_str[i:i + 2] in day_map:
                found_days.add(day_map[days_str[i:i + 2]])
                i += 2
            # Check for 3-character abbreviations
            elif i + 3 <= n and days_str[i:i + 3] in day_map:
                found_days.add(day_map[days_str[i:i + 3]])
                i += 3
            # Check for longer day names (like "Monday")
            else:
                matched = False
                for length in [4, 5, 6, 7, 8]:  # Cover all possible day name lengths
                    if i + length <= n and days_str[i:i + length] in day_map:
                        found_days.add(day_map[days_str[i:i + length]])
                        i += length
                        matched = True
                        break
                if not matched:
                    i += 1  # Skip unrecognized characters

        return sorted(found_days, key=lambda x: ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'].index(x))