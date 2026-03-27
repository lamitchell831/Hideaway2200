# Atera Remote Script Library

## Script Templates for Common Issues

### disk-cleanup.ps1
```powershell
# Clean temp files, recycle bin, Windows Update cache
Get-ChildItem "C:\Windows\Temp\*" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
Get-ChildItem "C:\Users\*\AppData\Local\Temp\*" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
Stop-Service wuauserv -Force
Remove-Item C:\Windows\SoftwareDistribution\Download\* -Recurse -Force -ErrorAction SilentlyContinue
Start-Service wuauserv
```

### memory-diagnostics.ps1
```powershell
# Check memory usage and top processes
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 Name, WorkingSet, CPU
```

### restart-service.ps1
```powershell
# Restart common problematic services
Restart-Service Spooler -Force
Restart-Service BITS -Force
Restart-Service wuauserv -Force
```

### patch-check.ps1
```powershell
# Check pending Windows updates
$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()
$updates = $searcher.Search("IsInstalled=0")
$updates.Updates | Select-Object Title, IsDownloaded
```

## Usage
When device health issues detected:
1. Identify issue type
2. Select appropriate script
3. Send Telegram with "Run on [Device]: [Script Name]"
4. Wait for approval
5. Execute via Atera API
