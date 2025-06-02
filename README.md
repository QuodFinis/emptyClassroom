# Empty Classrooms Finder

A web application that helps students find available classrooms at CUNY colleges. The application scrapes class schedules from the CUNY Global Search Tool, processes the data, and provides a user-friendly interface to find empty classrooms.

## Features

- View available classrooms in real-time
- Filter by college and building
- Book classrooms for study sessions
- User authentication and profile management
- Email verification for new accounts

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)

## Installation

1. Clone the repository (or download and extract the ZIP file):
   ```bash
   git clone https://github.com/yourusername/emptyClassroom.git
   cd emptyClassroom
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root directory with the following content:
   ```
   GMAIL_EMAIL=your-email@gmail.com
   GMAIL_PASSWORD=your-app-password
   ```
   Note: For Gmail, you'll need to use an App Password. See [Google's documentation](https://support.google.com/accounts/answer/185833) for instructions.

## Database Setup

1. Run migrations to create the database schema:
   ```bash
   python manage.py migrate
   ```

2. Create a superuser (admin) account:
   ```bash
   python manage.py createsuperuser
   ```

## Populating the Database with Class Schedules

The application uses a two-step process to populate the database with class schedules:

1. **Extract Schedule Data**: This step scrapes the CUNY Global Search Tool to get class schedules.
2. **Load Schedule Data**: This step imports the scraped data into the database and generates room availability information.

### Step 1: Extract Schedule Data

Run the extract_schedule.py script to scrape class schedules:

```bash
python classrooms/cunyScheduleETL/extract_schedule.py
```

By default, this will scrape data for City College. To scrape data for specific colleges, modify the college_names list in the script.

The script will create a CSV file named `cuny_schedule.csv` in the project root directory.

### Step 2: Load Schedule Data

Import the CSV data into the database:

```bash
python manage.py load_schedule cuny_schedule.csv
```

This command will:
1. Import the raw data into the ScheduleDump model
2. Process the data into normalized models (College, Building, Room, Schedule)
3. Generate room availability data

Optional arguments:
- `--skip-dump`: Skip saving to ScheduleDump model
- `--skip-normalized`: Skip processing to normalized models

## Running the Application

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:8000/
   ```

## Usage

### Finding Available Classrooms

1. On the homepage, you'll see a list of available classrooms.
2. Use the filters on the left to narrow down by college and building.
3. Click on a classroom to view details and book it (if logged in).

### Booking a Classroom

1. Log in to your account.
2. Find an available classroom and click on it.
3. On the classroom details page, use the booking form to reserve the room.
4. Bookings can be made for up to 1 hour, starting from the current time.

### Managing Your Bookings

1. Go to the "My Bookings" page to view your active and upcoming bookings.
2. You can cancel bookings from this page if needed.

## Development

### Running Tests

To run all tests:
```bash
python manage.py test
```

To run specific test classes:
```bash
python manage.py test classrooms.tests.LoginTestCase
python manage.py test classrooms.tests.PasswordResetTestCase
python manage.py test classrooms.tests.IntegrationTestCase
```

### Project Structure

- `classrooms/`: Main Django app
  - `cunyScheduleETL/`: Scripts for extracting class schedules
  - `management/commands/`: Custom Django management commands
  - `migrations/`: Database migrations
  - `models.py`: Database models
  - `views.py`: View functions
  - `templates/`: HTML templates
  - `tests/`: Test cases
- `emptyClassroom/`: Django project settings

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- CUNY Global Search Tool for providing class schedule data
- Django framework and community