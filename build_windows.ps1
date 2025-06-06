# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Please run this script as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Check if Python 3.12 is installed
if (-not (Test-Command python)) {
    Write-Host "Python not found. Installing Python 3.12..." -ForegroundColor Yellow
    
    # Download Python 3.12 installer
    $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
    $installerPath = "$env:TEMP\python-3.12.0-amd64.exe"
    
    Write-Host "Downloading Python 3.12 installer..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath
    
    # Install Python with PATH option
    Write-Host "Installing Python 3.12..." -ForegroundColor Yellow
    Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
    
    # Clean up installer
    Remove-Item $installerPath
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Check if Poetry is installed
if (-not (Test-Command poetry)) {
    Write-Host "Poetry not found. Installing Poetry..." -ForegroundColor Yellow
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Verify Python version
$pythonVersion = python --version
Write-Host "Using $pythonVersion" -ForegroundColor Green

# Install project dependencies
Write-Host "Installing project dependencies..." -ForegroundColor Yellow
poetry install

# Build the executable
Write-Host "Building executable..." -ForegroundColor Yellow
poetry run pyinstaller polyword.spec

# Check if build was successful
if (Test-Path "dist\PolyWord.exe") {
    Write-Host "`nBuild successful!" -ForegroundColor Green
    Write-Host "The executable is located at: $((Get-Item "dist\PolyWord.exe").FullName)" -ForegroundColor Green
    Write-Host "`nTo run the application:" -ForegroundColor Yellow
    Write-Host "1. Copy gcpkey.json to the dist directory" -ForegroundColor Yellow
    Write-Host "2. Double-click PolyWord.exe" -ForegroundColor Yellow
} else {
    Write-Host "Build failed. Please check the error messages above." -ForegroundColor Red
}

# Wait for user input before closing
Write-Host "`nPress Enter to exit..." -ForegroundColor Cyan
Read-Host 