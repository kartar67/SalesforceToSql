from simple_salesforce import Salesforce
from pathlib import Path
import pyodbc

# Configurable Parameters
specific_tables = ['Contact', 'User', 'Account']  # Add your table names here
output_folder = 'C:/temp/salesforce_objects'
row_limit = 10 # Limit for rows to fetch from Salesforce against the above tables
row_limit_csv = 10 # Limit for CSV's to ensure that the CSV's do not get large

# SQL Server connection details
sql_server = ''
sql_database = ''
sql_username = ''
sql_password = ''

# Salesforce credentials
sf_username = '' # Username for Salesforce account
sf_password = '' # Password for Salesforce account
sf_token = '' # Security Token for user account
sf_instance = '' # URL to login to Salesforce

# Mapping Salesforce field types to SQL data types
sf_to_sql_datatypes = {
    'datetime': 'datetime',
    'id': 'nvarchar(50)',
    'boolean': 'bit'
    # Add more mappings for other Salesforce field types as needed
}

# Default SQL data type for unknown Salesforce field types
default_sql_datatype = 'nvarchar(max)'

# Function to check if a field is compound
def is_compound_field(field):
    return field['type'] in ('address','Attachment')  # Adjust the condition based on Salesforce compound field types

# Connect to Salesforce
sf = Salesforce(username=sf_username, password=sf_password, security_token=sf_token, instance=sf_instance)

# Iterate through the specific tables and check for LastModifiedDate field
for table_name in specific_tables:
    fields = sf.__getattr__(table_name).describe()['fields']
    non_compound_fields = [field for field in fields if not is_compound_field(field)]
    
    if any(field['name'] == 'LastModifiedDate' for field in non_compound_fields):
        field_names = [field['name'] for field in non_compound_fields]

        # Construct the formatted field names with data types
        field_info = []
        for field in non_compound_fields:
            sf_field_type = field['type']
            sql_data_type = sf_to_sql_datatypes.get(sf_field_type, default_sql_datatype)
            field_info.append(f"[{field['name']}] {sql_data_type}")
        
        # Fields with sqldatatype for Create Table Statement
        sql_fields = ', '.join(field_info)

        # Establish a connection to SQL Server
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={sql_server};'
            f'DATABASE={sql_database};'
            f'UID={sql_username};'
            f'PWD={sql_password};'
            f'Encrypt=yes;'
        )
        conn = pyodbc.connect(conn_str)
        
        # Create table if not exists
        cr_table = f'''
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}')
            CREATE TABLE [{table_name}] ({sql_fields} );
        '''
        conn.execute(cr_table)
        conn.commit()
        
        # Query to fetch LastModifiedDate if exists, else return 0
        sql_query = f'''
        IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}')
        BEGIN
            IF EXISTS (SELECT 1 FROM dbo.[{table_name}])
            BEGIN
                SELECT ISNULL(MAX(LastModifiedDate), 0) AS max_date FROM dbo.[{table_name}]
            END
            ELSE
            BEGIN     
                SELECT 0 AS max_date
            END
        END
        '''

        # Execute the SQL query to fetch the last date
        cursor = conn.cursor()
        cursor.execute(sql_query)
        max_date = cursor.fetchone()[0]  # Assuming the date is in the first column

        cursor.close()  # Close the cursor
        conn.close()  # Close the connection

        # Copy full table if no value is found in maxdate
        if max_date == 0:
            query = f'''SELECT {', '.join(field_names)} from {table_name} ORDER BY LastModifiedDate ASC LIMIT {row_limit}'''
        else:
        # Copy delta rows if a date is found with a condition to match the lastmodifieddate >=
            # Format datetime object to ISO 8601 format with timezone information
            output_date_str = max_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            query = f'''SELECT {', '.join(field_names)} from {table_name} WHERE LastModifiedDate >= {output_date_str} ORDER BY LastModifiedDate ASC LIMIT {row_limit}'''
        
        # Create the directory if it doesn't exist
        directory_path = f'{output_folder}/{table_name}'
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)

        # Dump data locally in Csv's
        sf.bulk2.Account.download(
            query, path=f'{output_folder}/{table_name}', max_records=f'{row_limit_csv}'
        )