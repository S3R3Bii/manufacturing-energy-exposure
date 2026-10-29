param([string]$Uri, [string]$OutFile)
$ErrorActionPreference = 'Stop'
Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $OutFile -TimeoutSec 45
