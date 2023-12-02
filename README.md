# SalesforceToSql
**Data Transfer From Salesforce to MS SQL Server**

This is a simple tool that copied data from Salesforce to MS SQL Server. This handles the below:-
1. Python - Automatic schema creation for Salesforce Table on SQL Server.
2. Python - Dump Salesforce tables to CSV's using Bulk API 2.0
3. Powershell - Import CSV's using dbatools.io to SQL Server

**Requirements**
1. Install dbatools.io with the Powershell command Install-Module dbatools
2. Install ODBC Driver 17 For SQL Server. If you have 18 or a latest one then the Python code would need to be changed for this version.
3. Install requirements.txt for Python using the command pip install -r requirements.txt

**Getting Started**
1. Modify Configurable Parameters, SQL Server connection details and Salesforce credentials in the python code and run to dump CSV's of data for the tables that are mentioned.
2. Modify Configurable Parameters and SQL Server connection details in the powershell code to ingest data to SQL Server.


Though the code is self descriptive, I would highlight a few things that would be important to get started:-
1. The code has been tested on Windows only.
2. Credentials, Variables, Folder to dump csv to, and tables to export/import are all left blank in the script and are empty strings which would need to be replaced.
3. Test the code first with a smaller batch to ensure that the flow is understood.
4. This only copies data from tables which have LastModifiedDate column in Salesforce. You would need to manually modify the code to handle this if needed to dump all tables.
5. Compound fields are not supported by Bulk API, hence they are excluded from the final export. This is handled via the function is_compound_field.
6. sf_to_sql_datatypes handles datatype mapping from Salesforce to SQL. I find the list to be convenient as the data pipeline breaks if datatypes do not match. If you do require an index on any of the nvarchar(max) columns then I would recommend to manually change the schema of the table afterwards.
7. The code is restricted to a max limit of rows being dumped with the variable row_limit. If this is set to a high number then probably the whole table would be dumped in CSV.
8. The code picks delta in such a way that a few duplicates would be copied over and does not handle updates to the existing rows which were already copied to SQL and later updated in Salesforce. These would be duplicated too. You would need to handle the duplicacy of rows in the Select statement to pick the latest data and delete duplicates if not needed or apply distinct.
9. Since my intentions were only to use this as reporting, the schema has not been performance optimized. You can consider applying Clustered Columnstore Index to save space though.
10. The code has been divided into two parts as below:-
    10a. Python handles the csv downloads from Salesforce for the required tables.
    10b. Powershell handles the data ingestion to SQL.
11. Reason for the above is that I found python to be slow in data ingestion since there is no SQLBulkCopy class that is supported. There are ways to optimize inserts in python however, they are not as effective as SQLBulkCopy, hence, a separate powershell code. This gives the flexibility to dump from Salesforce and Ingest in SQL simultaneously or one after the another as needed.
12. For all CSV's processed by Powershell, they are renames with a prefix and that is removed if there are any errors during SQL insert to avoid data miss.