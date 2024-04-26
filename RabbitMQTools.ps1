# Install RabbitMQTools module if not installed
if (-not (Get-Module RabbitMQTools -ListAvailable)) {
    Install-Module RabbitMQTools -Scope CurrentUser -Force
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
        "Message" = $message
    }

    # Convert the parsed information to JSON format and save it to a file
    $parsedInfo | ConvertTo-Json | Out-File -FilePath $outputFilePath -Force
}

# Get queue names from user input
$QueueName = Read-Host "Enter queue name"

# Set RabbitMQ connection parameters
$BaseUri = "https://rabbitmq-tst.loxxitone.loxxess.com"
$VirtualHost = "BorC3"
$User = "Lx1Admin"
$Password = "fFIGSCMVdyc5SyhYO2Mr"

# Connect to RabbitMQ server and retrieve messages from queue
$RabbitMQParams = @{
    Credentials = New-Object System.Management.Automation.PSCredential ($User, ($Password | ConvertTo-SecureString -AsPlainText -Force))
    VirtualHost = $VirtualHost
    BaseUri = $BaseUri
}

try {
    $message = Get-RabbitMQMessage -QueueName $QueueName @RabbitMQParams
    if ($message -ne $null) {
        # Call Parse-JSON function to parse the message
        Parse-JSON -JSON $message.Body
    } else {
        Write-Host "No message found in the queue '$QueueName'."
    }
} catch {
    Write-Host "Failed to retrieve message from queue '$QueueName'. Error: $_"
}
