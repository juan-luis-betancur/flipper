# Prueba POST /api/cron/daily-scrape (mismo contrato que el programador diario).
# Ejemplo:
#   $env:FLIPPER_API_BASE_URL = "https://tu-backend.example.com"
#   $env:CRON_SECRET = "el-mismo-valor-que-en-produccion"
#   .\scripts\test_daily_scrape_endpoint.ps1

$ErrorActionPreference = "Stop"
if (-not $env:FLIPPER_API_BASE_URL) {
    Write-Error "Falta FLIPPER_API_BASE_URL (ej. https://tu-servicio.railway.app, sin barra final)"
}
if (-not $env:CRON_SECRET) {
    Write-Error "Falta CRON_SECRET (debe coincidir con el del servidor)"
}
$base = $env:FLIPPER_API_BASE_URL.TrimEnd("/")
$uri = "$base/api/cron/daily-scrape"
Write-Host "POST $uri"
$headers = @{ "X-Cron-Secret" = $env:CRON_SECRET }
try {
    $res = Invoke-WebRequest -Uri $uri -Method POST -Headers $headers -UseBasicParsing
    Write-Host "HTTP $($res.StatusCode)"
    Write-Host $res.Content
} catch {
    $r = $_.Exception.Response
    if ($r) {
        $reader = New-Object System.IO.StreamReader($r.GetResponseStream())
        $body = $reader.ReadToEnd()
        Write-Host "HTTP $([int]$r.StatusCode)"
        Write-Host $body
    }
    throw
}
