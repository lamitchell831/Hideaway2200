# Disk Cleanup Script for Atera
# Run this on Windows devices with low disk space

# Clean temp files
Get-ChildItem "C:\Windows\Temp\*" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
Get-ChildItem "C:\Users\*\AppData\Local\Temp\*" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue

# Clean Windows Update cache
Stop-Service wuauserv -Force
Remove-Item C:\Windows\SoftwareDistribution\Download\* -Recurse -Force -ErrorAction SilentlyContinue
Start-Service wuauserv

# Empty Recycle Bin
Clear-RecycleBin -Force -ErrorAction SilentlyContinue

# Clean browser caches
Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\INetCache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:LOCALAPPDATA\Google\Chrome\User Data\*\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue

# Check free space after cleanup
Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object @{Name="FreeSpaceGB";Expression={[math]::Round($_.FreeSpace/1GB,2)}}, @{Name="SizeGB";Expression={[math]::Round($_.Size/1GB,2)}}

Write-Output "Disk cleanup completed"
