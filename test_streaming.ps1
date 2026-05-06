# test_streaming.ps1
# Streams a 2-min podcast through Chatterbox and measures real performance:
#   - Time to first byte (TTFB): when does audio start arriving?
#   - Per-chunk timing: is delivery smooth or bursty?
#   - Real-time factor (RTF): is generation faster than playback?
#
# Usage: powershell -ExecutionPolicy Bypass -File .\test_streaming.ps1

# ============================================================
# CONFIG
# ============================================================
$URL = "https://agencympire--chatterbox-tts-streaming-chatterboxstreamin-6d5dad.modal.run"
$KEY = "REDACTED"
$SECRET = "REDACTED"
$TEXT_FILE = ".\podcast.txt"
$OUTPUT = ".\podcast_streaming.wav"
# ============================================================

if (-not (Test-Path $TEXT_FILE)) {
    Write-Host "ERROR: $TEXT_FILE not found in current folder" -ForegroundColor Red
    exit 1
}

$text = (Get-Content $TEXT_FILE -Raw).Trim()
Write-Host "Loaded $($text.Length) characters of text" -ForegroundColor Cyan

$body = @{
    text         = $text
    exaggeration = 0.7
    cfg_weight   = 0.4
    chunk_size   = 25
} | ConvertTo-Json -Compress

# Use HttpClient for true streaming (Invoke-WebRequest buffers the whole response)
Add-Type -AssemblyName System.Net.Http

$client = [System.Net.Http.HttpClient]::new()
$client.Timeout = [TimeSpan]::FromMinutes(10)

$req = [System.Net.Http.HttpRequestMessage]::new(
    [System.Net.Http.HttpMethod]::Post, $URL
)
$req.Headers.Add("Modal-Key", $KEY)
$req.Headers.Add("Modal-Secret", $SECRET)
$req.Content = [System.Net.Http.StringContent]::new(
    $body, [System.Text.Encoding]::UTF8, "application/json"
)

Write-Host ""
Write-Host "Sending request to streaming endpoint..." -ForegroundColor Cyan
$startTime = Get-Date

$resp = $client.SendAsync(
    $req, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead
).Result

if (-not $resp.IsSuccessStatusCode) {
    Write-Host "ERROR: $($resp.StatusCode) - $($resp.ReasonPhrase)" -ForegroundColor Red
    exit 1
}

$headersTime = ((Get-Date) - $startTime).TotalSeconds
Write-Host ("Headers received: {0:N2}s" -f $headersTime) -ForegroundColor Green

$stream = $resp.Content.ReadAsStreamAsync().Result
$out = [System.IO.File]::Create($OUTPUT)

$buffer = [byte[]]::new(8192)
$totalBytes = 0
$chunkNum = 0
$firstByteTime = $null
$lastReportTime = 0

while (($read = $stream.Read($buffer, 0, $buffer.Length)) -gt 0) {
    if ($null -eq $firstByteTime) {
        $firstByteTime = ((Get-Date) - $startTime).TotalSeconds
        Write-Host ("FIRST BYTE: {0:N2}s  <- this is the TTFB" -f $firstByteTime) -ForegroundColor Yellow
        Write-Host ""
    }
    $out.Write($buffer, 0, $read)
    $totalBytes += $read
    $chunkNum++

    $elapsed = ((Get-Date) - $startTime).TotalSeconds
    if ($elapsed - $lastReportTime -ge 1.0) {
        $audioSec = $totalBytes / 48000
        $progressRtf = if ($audioSec -gt 0) { $elapsed / $audioSec } else { 0 }
        Write-Host ("  [{0,5:N2}s wall] chunks={1,4} bytes={2,8:N0} audio~{3,5:N1}s RTF={4:N2}" `
            -f $elapsed, $chunkNum, $totalBytes, $audioSec, $progressRtf) -ForegroundColor Gray
        $lastReportTime = $elapsed
    }
}

$out.Close()
$stream.Close()
$client.Dispose()

$totalTime = ((Get-Date) - $startTime).TotalSeconds
$audioDuration = ($totalBytes - 44) / 48000
$rtf = $totalTime / $audioDuration

Write-Host ""
Write-Host "============= STREAMING RESULTS =============" -ForegroundColor Cyan
Write-Host ("Time to first byte:   {0,6:N2}s" -f $firstByteTime)
Write-Host ("Total wall time:      {0,6:N2}s" -f $totalTime)
Write-Host ("Audio duration:       {0,6:N2}s" -f $audioDuration)
Write-Host ("Real-time factor:     {0,6:N3}  (lower is better, < 1.0 = faster than realtime)" -f $rtf)
Write-Host ("Total bytes written:  {0:N0}" -f $totalBytes)
Write-Host ("Total chunks:         {0}" -f $chunkNum)
Write-Host "============================================="
Write-Host ""

if ($firstByteTime -lt 1.0) {
    Write-Host "TTFB under 1s: excellent for live agents." -ForegroundColor Green
} elseif ($firstByteTime -lt 3.0) {
    Write-Host "TTFB 1-3s: acceptable for non-realtime use." -ForegroundColor Yellow
} else {
    Write-Host "TTFB over 3s: this is a cold start. Run again to see warm performance." -ForegroundColor Yellow
}

if ($rtf -lt 1.0) {
    Write-Host "RTF under 1.0: generation is faster than playback. Streaming will never stutter." -ForegroundColor Green
} else {
    Write-Host "RTF over 1.0: generation slower than playback. Stream will stall on long content." -ForegroundColor Red
}

Write-Host ""
Write-Host "Saved to: $OUTPUT" -ForegroundColor Green
