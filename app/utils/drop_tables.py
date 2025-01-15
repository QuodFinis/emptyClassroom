import pyodbc
from pathlib import Path
from config import DB_HOST, DB_NAME, DB_USERNAME, DB_PASSWORD, DB_DRIVER, DB_ENCRYPT, DB_TRUST_SERVER_CERT

def drop_tables(tables):
    connection_string = (
        f'Driver={DB_DRIVER};'
        f'Server=tcp:{DB_HOST};'  
        f'Database={DB_NAME};'
        f'Uid={DB_USERNAME};'
        f'Pwd={DB_PASSWORD};'
        f'Encrypt={DB_ENCRYPT};'
        f'TrustServerCertificate={DB_TRUST_SERVER_CERT};'
        'Connection Timeout=30;'
    )

    connection = pyodbc.connect(connection_string)
    cursor = connection.cursor()

    # foreign key constraints are foreign keys that reference a table from another table
    # to drop a table, we need to drop all foreign key constraints that reference the table
    # foreign key constraints are dropped in reverse order of their creation
    for table in tables:
        query = f"""
        DECLARE @sql NVARCHAR(MAX) = N'';

        SELECT @sql += 'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(fk.parent_object_id))
                     + '.' + QUOTENAME(OBJECT_NAME(fk.parent_object_id))
                     + ' DROP CONSTRAINT ' + QUOTENAME(fk.name) + ';' + CHAR(13)
        FROM sys.foreign_keys AS fk
        WHERE OBJECT_NAME(fk.referenced_object_id) = '{table}';

        EXEC sp_executesql @sql;
        """
        print(f"Dropping foreign keys referencing table: {table}")
        cursor.execute(query)
        cursor.commit()

    # Drop tables
    for table in tables:
        drop_query = f"DROP TABLE IF EXISTS [dbo].[{table}];"
        print(f"Dropping table: {table}")
        cursor.execute(drop_query)
        cursor.commit()

    cursor.close()
    connection.close()

    # Clear the migration scripts in the migrations folder (app/migrations)
    migrations_folder = Path('app/migrations')
    for migration_file in migrations_folder.glob('*.py'):
        if migration_file.name != '__init__.py':
            migration_file.unlink()

    print("Tables dropped successfully!")


if __name__ == '__main__':
    tables = [
        'app_building',
        'app_course',
        'app_days',
        'app_department',
        'app_floor',
        'app_professor',
        'app_room',
        'app_schedule',
        'app_school',
        'app_professor_departments',
        'app_uploadedfilestatus',

        'auth_group',
        'auth_group_permissions',
        'auth_permission',
        'auth_user',
        'auth_user_groups',
        'auth_user_user_permissions',

        'django_admin_log',
        'django_content_type',
        'django_migrations',
        'django_session',
    ]

    drop_tables(tables)

    # run command to create migration and migrate
    # python manage.py makemigrations
    # python manage.py migrate