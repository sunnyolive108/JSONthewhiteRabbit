# Get the directory of the script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# import RabbitMQ configurations from config\config.ini
$configFile = Join-Path $scriptDir "config\config.ini"

if (-not (Test-Path $configFile)) {
    Write-Host "config.ini not found in '$configFile'"
    exit
}

$configContent = Get-Content $configFile -Raw

$rabbitmqConfig = @{
    username = ""
    password = ""
    host = ""
    virtual_host = ""
}

# Function to parse JSON and extract crucial information
function Parse-JSON {
    param (
        [string]$JSON
    )
    $parsedJSON = ConvertFrom-Json $JSON
    $exceptionList = @{}
    $messageInfo = @{}

    # Extracting exception information
    $exception = $parsedJSON.exception

    # Truncate exception message if it's longer than 313 characters
    if ($exception.Length -gt 313) {
        $exceptionTruncated = $exception.Substring(0, 313)
    }
    else {
        $exceptionTruncated = $exception
    }

    # Counting frequency of each exception
    if ($exceptionList.ContainsKey($exceptionTruncated)) {
        $exceptionList[$exceptionTruncated]++
    }
    else {
        $exceptionList[$exceptionTruncated] = 1
    }

    # Extracting message information
    $message = ConvertFrom-Json $parsedJSON.message

    # Extracting and formatting the dateCreated part from the message
    $dateCreated = [datetime]::ParseExact($message.DateCreated, "MM/dd/yyyy HH:mm:ss", $null)
    $datePrefix = $dateCreated.ToString("yyyyMMdd")

    # Output crucial information to the terminal
    Write-Output ""
    Write-Output "------------------------------------------"
    Write-Output "Exception: $exceptionTruncated"
    Write-Output "Message:"
    $message | Get-Member -MemberType NoteProperty | ForEach-Object {
        $key = $_.Name
        $value = $message.($_.Name)
        Write-Output "${key}: $value"
    }
    Write-Output "------------------------------------------"

    # Create a folder to store JSON files if it doesn't exist
    $folderPath = ".\Parsed_JSON_Files"
    if (-not (Test-Path -Path $folderPath)) {
        New-Item -ItemType Directory -Path $folderPath | Out-Null
    }

    # Generate the file name
    $fileNamePrefix = $datePrefix + "_" + ($exceptionTruncated -replace '[^a-zA-Z]').Substring(0, [Math]::Min(21, ($exceptionTruncated -replace '[^a-zA-Z]').Length))
    $fileName = "{0}.json" -f $fileNamePrefix

    # Output crucial information to a separate file
    $outputFilePath = Join-Path -Path $folderPath -ChildPath $fileName
    $parsedInfo = @{
        "Exception" = $exceptionTruncated
        "DateCreated" = $dateCreated.ToString("yyyy-MM-dd")
        "Message" = $message
    }

    # Convert the parsed information to JSON format and save it to a file
    $parsedInfo | ConvertTo-Json | Out-File -FilePath $outputFilePath -Force
}

# Prompt user for JSON input
$jsonInput = Read-Host "Enter JSON input"

# Call the function with the user-provided JSON input
Parse-JSON -JSON $jsonInput
