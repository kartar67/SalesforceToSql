# SQL Server connection details
$sql_server = ''
$sql_database = ''
$sql_username = ''
$sql_password = ''
$secureString = ConvertTo-SecureString -AsPlainText -Force -String $sql_password
$credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $sql_username, $secureString

# Configurable Parameters
$tablename = @("Contact", "User", "Account")
$parent_directory = 'C:\temp\salesforce_objects'

try 
{
    #Process a single table with pending CSV's
    foreach($table in $tablename)
    {
        $output_folder = "$parent_directory\$table"
        $combinedData = @()

        $files = (Get-Item -Path "$output_folder\*.csv" -Exclude 'zz_processed_*' | Where-Object $_.Length -ne 0).Name
        if($files)
        {
            foreach($file in $files)
            {
                $csv = Import-Csv -Path "$output_folder\$file"
                write-host $file
                Rename-Item -Path "$output_folder\$file" -NewName "$output_folder\zz_processed_$file"
                $combinedData += $csv
            }

            #Write all the unprocessed CSV's to the table. The size of CSV's being processed should be minimal or low as they consume resources during datatable creation
            Write-DbaDbTableData -SqlInstance $sql_server -BatchSize 2000 -SqlCredential $credential -Database $sql_database -InputObject $combinedData -Table "dbo.$table" -ErrorAction Stop -WarningAction Stop
        }
}
}
catch {
    foreach($file in $files)
    {
        Rename-Item -Path "$parent_directory/zz_processed_$file" -NewName "$parent_directory/$file"
    }
    throw ('Exception')
}