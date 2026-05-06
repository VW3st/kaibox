# load_env.ps1
# Reads .env file and sets environment variables for the current session.
# Sourced by other scripts via:  . .\load_env.ps1

if (-not (Test-Path .\.env)) {
    Write-Host "ERROR: .env file not found in current folder." -ForegroundColor Red
    Write-Host "Copy .env.example to .env and fill in your tokens." -ForegroundColor Yellow
    exit 1
}

Get-Content .\.env | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#")) {
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $key = $parts[0].Trim()
            $value = $parts[1].Trim()
            Set-Item -Path "env:$key" -Value $value
        }
    }
}
