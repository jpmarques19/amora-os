# dev.ps1 - Development script for Python Waybox Player
# This script provides options to start the container in dev mode or run tests locally
#
# Usage:
#   .\dev.ps1                      - Interactive menu mode
#   .\dev.ps1 -Start               - Start container in dev mode
#   .\dev.ps1 -Test                - Run tests locally with coverage
#   .\dev.ps1 -Build               - Build container image
#   .\dev.ps1 -Clean               - Clean up containers

param(
    [Parameter(Mandatory=$false)]
    [switch]$Start,

    [Parameter(Mandatory=$false)]
    [switch]$Test,

    [Parameter(Mandatory=$false)]
    [switch]$Build,

    [Parameter(Mandatory=$false)]
    [switch]$Clean
)

# Global variables
$script:LogFile = $null
$script:LogsFolder = Join-Path $PSScriptRoot "logs"
$script:MaxLogFiles = 3

function Initialize-Logging {
    # Create logs directory if it doesn't exist
    if (-not (Test-Path -Path $script:LogsFolder)) {
        New-Item -Path $script:LogsFolder -ItemType Directory | Out-Null
        Write-Host "Created logs directory at $script:LogsFolder" -ForegroundColor Yellow
    }

    # Create a new log file with timestamp
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $script:LogFile = Join-Path $script:LogsFolder "waybox_dev_${timestamp}.log"

    # Add header to log file
    $header = @"
===============================================================
Python Waybox Player - Development Log
Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
===============================================================

"@
    Add-Content -Path $script:LogFile -Value $header

    # Clean up old log files
    Cleanup-OldLogs
}

function Cleanup-OldLogs {
    # Get all log files sorted by creation time (newest first)
    $logFiles = Get-ChildItem -Path $script:LogsFolder -Filter "waybox_dev_*.log" |
                Sort-Object CreationTime -Descending

    # Keep only the most recent logs (specified by MaxLogFiles)
    if ($logFiles.Count -gt $script:MaxLogFiles) {
        $filesToRemove = $logFiles | Select-Object -Skip $script:MaxLogFiles
        foreach ($file in $filesToRemove) {
            Remove-Item -Path $file.FullName -Force
            Write-Host "Removed old log file: $($file.Name)" -ForegroundColor DarkGray
        }
    }
}

function Write-Log {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,

        [Parameter(Mandatory=$false)]
        [string]$ForegroundColor = "White"
    )

    # Write to console
    Write-Host $Message -ForegroundColor $ForegroundColor

    # Write to log file
    if ($script:LogFile) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Add-Content -Path $script:LogFile -Value "[$timestamp] $Message"
    }
}

function Show-Menu {
    Clear-Host
    Write-Host "================ Python Waybox Player - Dev Tools ================"
    Write-Host "1: Start container in dev mode (Windows audio host)"
    Write-Host "2: Run tests locally with coverage"
    Write-Host "3: Build container image"
    Write-Host "4: Clean up (stop and remove containers)"
    Write-Host "Q: Quit"
    Write-Host "================================================================="

    if ($script:LogFile) {
        Write-Host "Logging to: $script:LogFile" -ForegroundColor DarkGray
    }
}

function Start-DevContainer {
    Write-Host "Starting container in dev mode (Windows audio host)..." -ForegroundColor Cyan

    # Check if container already exists
    $containerExists = docker ps -a --filter "name=waybox-player-python-dev" --format "{{.Names}}"

    if ($containerExists) {
        Write-Host "Container already exists. Stopping and removing..." -ForegroundColor Yellow
        docker stop waybox-player-python-dev
        docker rm waybox-player-python-dev
    }

    # Create samples directory if it doesn't exist
    if (-not (Test-Path -Path ".\samples")) {
        Write-Host "Creating samples directory..." -ForegroundColor Yellow
        New-Item -Path ".\samples" -ItemType Directory | Out-Null
        New-Item -Path ".\samples\playlists" -ItemType Directory | Out-Null

        # Create sample README file
        $readmeContent = "# Sample Music Files`n`nThis directory contains sample files for testing the Waybox Player in development mode.`n`nAdd MP3 files here for testing."
        Set-Content -Path ".\samples\README.md" -Value $readmeContent

        # Create sample text files (placeholders for MP3 files)
        Set-Content -Path ".\samples\sample1.txt" -Value "This is a sample MP3 file (text representation for testing)."
        Set-Content -Path ".\samples\sample2.txt" -Value "This is another sample MP3 file (text representation for testing)."
        Set-Content -Path ".\samples\playlists\test_playlist.txt" -Value "This is a test playlist file."
    }

    # Start container in dev mode
    Write-Host "Starting container..." -ForegroundColor Green
    docker run -d --name waybox-player-python-dev `
        -v "${PWD}/samples:/home/user/music" `
        -v "${PWD}/src:/home/user/app/src" `
        -v "${PWD}/config:/home/user/app/config" `
        -v "${PWD}/scripts:/home/user/app/scripts" `
        -p 6600:6600 `
        -p 4713:4713 `
        --add-host=host.docker.internal:host-gateway `
        waybox-python-player /home/user/start.sh

    # Wait for container to start
    Start-Sleep -Seconds 2

    # Ensure permissions are correct for the music directory
    Write-Host "Ensuring music directory permissions are correct..." -ForegroundColor Yellow
    docker exec waybox-player-python-dev bash -c "sudo chmod -R 777 /home/user/music && sudo chown -R user:user /home/user/music && ls -la /home/user/music"

    # Update MPD database to recognize the music files
    Write-Host "Updating MPD database..." -ForegroundColor Yellow
    docker exec waybox-player-python-dev bash -c "mpc update"

    # Make play-sample.sh script executable
    Write-Host "Making play-sample.sh script executable..." -ForegroundColor Yellow
    docker exec waybox-player-python-dev bash -c "chmod +x /home/user/app/scripts/play-sample.sh"

    # Check if container is running
    $containerRunning = docker ps --filter "name=waybox-player-python-dev" --format "{{.Names}}"

    if ($containerRunning) {
        Write-Host "Container started successfully!" -ForegroundColor Green
        Write-Host "Opening bash shell in container..." -ForegroundColor Cyan

        # Open bash shell in container
        docker exec -it waybox-player-python-dev /bin/bash

        # Log the completion but don't exit
        Write-Log "Operation completed." -ForegroundColor DarkGray
        return
    }
    else {
        Write-Host "Failed to start container. Check docker logs:" -ForegroundColor Red
        docker logs waybox-player-python-dev

        # Log the completion but don't exit
        Write-Log "Operation completed." -ForegroundColor DarkGray
        return
    }
}

function Run-LocalTests {
    Write-Host "Running tests locally with coverage..." -ForegroundColor Cyan

    # Define Poetry paths
    $poetryPath = "$env:APPDATA\Python\Scripts\poetry.exe"
    $poetryWindowsPath = "$env:USERPROFILE\AppData\Roaming\Python\Scripts\poetry.exe"
    $poetryLocalPath = "$env:LOCALAPPDATA\pypoetry\venv\Scripts\poetry.exe"

    # Check if Poetry is installed and find the executable
    $poetryExe = $null
    if (Test-Path $poetryPath) {
        $poetryExe = $poetryPath
    }
    elseif (Test-Path $poetryWindowsPath) {
        $poetryExe = $poetryWindowsPath
    }
    elseif (Test-Path $poetryLocalPath) {
        $poetryExe = $poetryLocalPath
    }

    # If Poetry not found, try to find it in PATH
    if (-not $poetryExe) {
        try {
            $poetryVersion = poetry --version
            $poetryExe = "poetry"
            Write-Host "Poetry found in PATH: $poetryVersion" -ForegroundColor Green
        }
        catch {
            Write-Host "Poetry not found. Installing Poetry..." -ForegroundColor Yellow

            # Install Poetry
            try {
                (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

                # Check common installation locations after install
                Start-Sleep -Seconds 2

                if (Test-Path $poetryPath) {
                    $poetryExe = $poetryPath
                }
                elseif (Test-Path $poetryWindowsPath) {
                    $poetryExe = $poetryWindowsPath
                }
                elseif (Test-Path $poetryLocalPath) {
                    $poetryExe = $poetryLocalPath
                }
                else {
                    # Try to find poetry in PATH after installation
                    try {
                        $poetryVersion = poetry --version
                        $poetryExe = "poetry"
                    }
                    catch {
                        Write-Host "Poetry installed but executable not found. Please restart PowerShell or add Poetry to your PATH manually." -ForegroundColor Red
                        Write-Host "Common locations to check:" -ForegroundColor Yellow
                        Write-Host "  - $poetryPath" -ForegroundColor Yellow
                        Write-Host "  - $poetryWindowsPath" -ForegroundColor Yellow
                        Write-Host "  - $poetryLocalPath" -ForegroundColor Yellow

                        # Log the error but don't exit
                        Write-Log "Operation failed." -ForegroundColor DarkGray
                        return
                    }
                }
            }
            catch {
                Write-Host "Failed to install Poetry: $_" -ForegroundColor Red
                # Log the error but don't exit
                Write-Log "Operation failed." -ForegroundColor DarkGray
                return
            }
        }
    }

    Write-Host "Using Poetry at: $poetryExe" -ForegroundColor Green

    # Install dependencies if needed
    if (-not (Test-Path -Path ".\.venv")) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        & $poetryExe install

        if ($LASTEXITCODE -ne 0) {
            Write-Host "Failed to install dependencies. See output above for details." -ForegroundColor Red
            # Log the error but don't exit
            Write-Log "Operation failed." -ForegroundColor DarkGray
            return
        }
    }

    # Run tests with coverage
    Write-Host "Running tests with coverage..." -ForegroundColor Green
    & $poetryExe run pytest --cov=src --cov-report=term

    # Show result message
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Tests passed!" -ForegroundColor Green
    }
    else {
        Write-Host "Tests failed. See output above for details." -ForegroundColor Red
    }

    # Log the completion but don't exit
    Write-Log "Operation completed." -ForegroundColor DarkGray
    return
}

function Build-Container {
    Write-Host "Building container image..." -ForegroundColor Cyan

    # Clean up any existing images with the same name
    Write-Host "Cleaning up existing images..." -ForegroundColor Yellow
    docker image rm waybox-python-player -f 2>$null

    # Build the image with no cache
    Write-Host "Building new image with no cache..." -ForegroundColor Green
    docker build --no-cache -t waybox-python-player .

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Container image built successfully!" -ForegroundColor Green
    }
    else {
        Write-Host "Failed to build container image. See output above for details." -ForegroundColor Red
    }

    # Log the completion but don't exit
    Write-Log "Operation completed." -ForegroundColor DarkGray
    return
}

function Clean-Environment {
    Write-Host "Cleaning up environment..." -ForegroundColor Cyan

    # Stop and remove dev container if it exists
    $containerExists = docker ps -a --filter "name=waybox-player-python-dev" --format "{{.Names}}"
    if ($containerExists) {
        Write-Host "Stopping and removing dev container..." -ForegroundColor Yellow
        docker stop waybox-player-python-dev
        docker rm waybox-player-python-dev
    }

    # Stop and remove regular container if it exists
    $containerExists = docker ps -a --filter "name=waybox-player-python" --format "{{.Names}}"
    if ($containerExists) {
        Write-Host "Stopping and removing regular container..." -ForegroundColor Yellow
        docker stop waybox-player-python
        docker rm waybox-player-python
    }

    Write-Host "Environment cleaned up!" -ForegroundColor Green

    # Log the completion but don't exit
    Write-Log "Operation completed." -ForegroundColor DarkGray
    return
}

function Read-MenuChoice {
    $choice = Read-Host "Enter your choice"

    switch ($choice) {
        '1' { Start-DevContainer }
        '2' { Run-LocalTests }
        '3' { Build-Container }
        '4' { Clean-Environment }
        'q' { return }
        'Q' { return }
        default {
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            Start-Sleep -Seconds 1
            Show-Menu
            Read-MenuChoice
        }
    }
}

# Check if Docker is running
try {
    $dockerInfo = docker info
}
catch {
    Write-Host "Docker is not running or not installed. Please start Docker Desktop and try again." -ForegroundColor Red
    # Don't exit, just return to keep the terminal state
    return
}

# Main script execution
$script:LogFile = Initialize-Logging
Write-Log "Starting Python Waybox Player Dev Tools..." -ForegroundColor Green
Write-Log "Log file: $script:LogFile" -ForegroundColor DarkGray

# Check if any command-line parameters were provided
if ($Start -or $Test -or $Build -or $Clean) {
    # Execute the specified command directly
    if ($Start) {
        Write-Log "Command-line mode: Starting container in dev mode" -ForegroundColor Cyan
        Start-DevContainer
    }
    elseif ($Test) {
        Write-Log "Command-line mode: Running tests locally" -ForegroundColor Cyan
        Run-LocalTests
    }
    elseif ($Build) {
        Write-Log "Command-line mode: Building container image" -ForegroundColor Cyan
        Build-Container
    }
    elseif ($Clean) {
        Write-Log "Command-line mode: Cleaning up environment" -ForegroundColor Cyan
        Clean-Environment
    }
}
else {
    # No command-line parameters, show the interactive menu
    Show-Menu
    Read-MenuChoice
}

# Display a message at the end to indicate the script has completed but the terminal is still active
Write-Host "`n===================================================================" -ForegroundColor DarkGray
Write-Host "Script operation completed. Terminal is still active." -ForegroundColor Green
Write-Host "You can run another command or close this window manually." -ForegroundColor DarkGray
Write-Host "===================================================================" -ForegroundColor DarkGray
