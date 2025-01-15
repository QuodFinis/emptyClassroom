from pathlib import Path
from dotenv import load_dotenv
from os import getenv

# Load environment variables from .env.dev file (for local development)
env_path = Path('.') / '.env.dev'
load_dotenv(dotenv_path=env_path)

# Django settings
DJANGO_DEBUG = getenv('DEBUG', 'False').lower() == 'true'
DJANGO_SECRET_KEY = getenv('SECRET_KEY')

# Azure SQL Database
DB_HOST = getenv('DB_HOST')
DB_NAME = getenv('DB_NAME')
DB_PORT = getenv('DB_PORT', '1433')
DB_USERNAME = getenv('DB_USERNAME')
DB_PASSWORD = getenv('DB_PASSWORD')
DB_DRIVER = getenv('DB_DRIVER', 'ODBC Driver 18 for SQL Server')
DB_ENCRYPT = getenv('DB_ENCRYPT', 'true').lower()
DB_TRUST_SERVER_CERT = getenv('DB_TRUST_SERVER_CERTIFICATE', 'false').lower()
DB_TIMEOUT = int(getenv('DB_TIMEOUT', 30))

# Azure Blob Storage
BLOB_FILE_STORAGE = getenv('BLOB_FILE_STORAGE')
BLOB_STORAGE_ACC_NAME = getenv('BLOB')
BLOB_CONTAINER = getenv('BLOB_CONTAINER')
BLOB_CONTAINER_URL = getenv('BLOB_CONTAINER_URL')
BLOB_ACC_KEY = getenv('BLOB_ACCOUNT_KEY')
BLOB_CONN_STR = getenv('BLOB_CONNECTION_STRING')

# Azure Cache for Redis
REDIS_NAME = getenv('REDIS_DNS_NAME')
REDIS_ACCESS_KEY = getenv('REDIS_ACCESS_KEY')
REDIS_CONN_STR = getenv('REDIS_CONNECTION_STRING')
