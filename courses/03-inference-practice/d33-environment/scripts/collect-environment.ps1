$ErrorActionPreference = 'Continue'

Write-Output '[OS]'
Get-ComputerInfo |
    Select-Object WindowsProductName, WindowsVersion, OsBuildNumber, OsArchitecture |
    Format-List

Write-Output '[CPU]'
Get-CimInstance Win32_Processor |
    Select-Object Name, NumberOfCores, NumberOfLogicalProcessors |
    Format-List

Write-Output '[SYSTEM MEMORY]'
Get-CimInstance Win32_ComputerSystem |
    Select-Object @{N = 'TotalMemoryGiB'; E = { [math]::Round($_.TotalPhysicalMemory / 1GB, 2) }} |
    Format-List

Write-Output '[DISPLAY DEVICES]'
Get-CimInstance Win32_VideoController |
    Select-Object Name, DriverVersion |
    Format-Table -AutoSize

Write-Output '[NVIDIA GPU]'
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
} else {
    Write-Output 'nvidia-smi not found'
}

Write-Output '[WSL]'
wsl --status 2>&1
wsl -l -v 2>&1

Write-Output '[DOCKER]'
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker version --format 'Client={{.Client.Version}} Server={{.Server.Version}}' 2>&1
} else {
    Write-Output 'docker not found'
}

Write-Output '[PYTHON]'
if (Get-Command python -ErrorAction SilentlyContinue) {
    python --version
    (Get-Command python).Source
} else {
    Write-Output 'python not found'
}

Write-Output '[DISK]'
Get-PSDrive -PSProvider FileSystem |
    Select-Object Name,
        @{N = 'UsedGiB'; E = { [math]::Round($_.Used / 1GB, 1) } },
        @{N = 'FreeGiB'; E = { [math]::Round($_.Free / 1GB, 1) } } |
    Format-Table -AutoSize
