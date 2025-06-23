param(
    [string]$Version = "1.0.0"
)

$PackageName = "bytefense-os"
$ImageName = "bytefense-builder"
$ContainerName = "bytefense-build-temp"

Write-Host "Building .deb package using Docker" -ForegroundColor Green

# Verify Docker is available
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker detected: $dockerVersion" -ForegroundColor Green
    } else {
        throw "Docker not responding"
    }
} catch {
    Write-Host "Docker is not available. Please verify it's installed and running." -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Clean previous containers
Write-Host "Cleaning previous containers..." -ForegroundColor Yellow
docker rm -f $ContainerName 2>$null | Out-Null

# Build image
Write-Host "Building Docker image..." -ForegroundColor Yellow
docker build -f Dockerfile.deb -t $ImageName .

if ($LASTEXITCODE -eq 0) {
    Write-Host "Image built successfully" -ForegroundColor Green
    
    # Create output directory
    if (!(Test-Path "dist")) {
        New-Item -ItemType Directory -Path "dist" -Force | Out-Null
    }
    
    # Run container and extract files
    Write-Host "Extracting .deb package..." -ForegroundColor Yellow
    docker run --name $ContainerName -v "${PWD}\dist:/output" $ImageName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Container executed successfully" -ForegroundColor Green
        
        # Clean container
        docker rm $ContainerName | Out-Null
        
        # Verify result
        $DebFile = Get-ChildItem "dist\*.deb" | Select-Object -First 1
        if ($DebFile) {
            Write-Host "Package .deb created successfully:" -ForegroundColor Green
            Write-Host "File: $($DebFile.FullName)" -ForegroundColor Cyan
            Write-Host "Size: $([math]::Round($DebFile.Length / 1MB, 2)) MB" -ForegroundColor Cyan
            
            # Show package information
            Write-Host "Package information:" -ForegroundColor Yellow
            if (Get-Command dpkg -ErrorAction SilentlyContinue) {
                dpkg --info $DebFile.FullName
            } else {
                Write-Host "To see detailed information, install dpkg or run on Linux" -ForegroundColor Yellow
            }
        } else {
            Write-Host "Error: .deb file not found in dist/" -ForegroundColor Red
            Write-Host "Contents of dist/ directory:" -ForegroundColor Yellow
            Get-ChildItem "dist" -ErrorAction SilentlyContinue | Format-Table Name, Length, LastWriteTime
            exit 1
        }
    } else {
        Write-Host "Error executing container" -ForegroundColor Red
        Write-Host "Container logs:" -ForegroundColor Yellow
        docker logs $ContainerName 2>$null
        exit 1
    }
} else {
    Write-Host "Error building Docker image" -ForegroundColor Red
    exit 1
}

Write-Host "Process completed successfully" -ForegroundColor Green
Write-Host "The .deb package is ready in the dist/ directory" -ForegroundColor Cyan